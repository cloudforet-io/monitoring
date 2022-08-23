import logging

from spaceone.core.service import *
from spaceone.core import utils

from spaceone.monitoring.error import *
from spaceone.monitoring.model.webhook_model import Webhook
from spaceone.monitoring.manager.project_alert_config_manager import ProjectAlertConfigManager
from spaceone.monitoring.manager.repository_manager import RepositoryManager
from spaceone.monitoring.manager.webhook_plugin_manager import WebhookPluginManager
from spaceone.monitoring.manager.webhook_manager import WebhookManager

_LOGGER = logging.getLogger(__name__)


@authentication_handler
@authorization_handler
@mutation_handler
@event_handler
class WebhookService(BaseService):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.webhook_mgr: WebhookManager = self.locator.get_manager('WebhookManager')
        self.webhook_plugin_mgr: WebhookPluginManager = self.locator.get_manager('WebhookPluginManager')

    @transaction(append_meta={'authorization.scope': 'PROJECT'})
    @check_required(['name', 'plugin_info', 'project_id', 'domain_id'])
    def create(self, params):
        """Create webhook

        Args:
            params (dict): {
                'name': 'str',
                'plugin_info': 'dict',
                'project_id': 'str'
                'tags': 'dict',
                'domain_id': 'str'
            }

        Returns:
            webhook_vo (object)
        """

        domain_id = params['domain_id']
        project_id = params['project_id']

        project_alert_config_mgr: ProjectAlertConfigManager = self.locator.get_manager('ProjectAlertConfigManager')

        project_alert_config_mgr.get_project_alert_config(project_id, domain_id)

        self._check_plugin_info(params['plugin_info'])
        plugin_info = self._get_plugin(params['plugin_info'], domain_id)
        params['capability'] = plugin_info.get('capability', {})

        _LOGGER.debug(f'[create] Init Plugin: {params["plugin_info"]}')
        endpoint, updated_version = self.webhook_plugin_mgr.get_webhook_plugin_endpoint(params['plugin_info'], domain_id)
        if updated_version:
            params['plugin_info']['version'] = updated_version

        options = params['plugin_info'].get('options', {})
        plugin_metadata = self._init_plugin(endpoint, options)
        params['plugin_info']['metadata'] = plugin_metadata

        webhook_vo: Webhook = self.webhook_mgr.create_webhook(params)

        access_key = self._generate_access_key()
        webhook_url = self._make_webhook_url(webhook_vo.webhook_id, access_key)

        return self.webhook_mgr.update_webhook_by_vo({
            'access_key': access_key,
            'webhook_url': webhook_url
        }, webhook_vo)

    @transaction(append_meta={'authorization.scope': 'PROJECT'})
    @check_required(['webhook_id', 'domain_id'])
    def update(self, params):
        """Update webhook

        Args:
            params (dict): {
                'webhook_id': 'str',
                'name': 'dict',
                'tags': 'dict'
                'domain_id': 'str'
            }

        Returns:
            webhook_vo (object)
        """

        webhook_id = params['webhook_id']
        domain_id = params['domain_id']
        webhook_vo = self.webhook_mgr.get_webhook(webhook_id, domain_id)

        return self.webhook_mgr.update_webhook_by_vo(params, webhook_vo)

    @transaction(append_meta={'authorization.scope': 'PROJECT'})
    @check_required(['webhook_id', 'domain_id'])
    def enable(self, params):
        """ Enable webhook

        Args:
            params (dict): {
                'webhook_id': 'str',
                'domain_id': 'str'
            }

        Returns:
            webhook_vo (object)
        """

        webhook_id = params['webhook_id']
        domain_id = params['domain_id']
        webhook_vo = self.webhook_mgr.get_webhook(webhook_id, domain_id)

        return self.webhook_mgr.update_webhook_by_vo({'state': 'ENABLED'}, webhook_vo)

    @transaction(append_meta={'authorization.scope': 'PROJECT'})
    @check_required(['webhook_id', 'domain_id'])
    def disable(self, params):
        """ Disable webhook

        Args:
            params (dict): {
                'webhook_id': 'str',
                'domain_id': 'str'
            }

        Returns:
            webhook_vo (object)
        """

        webhook_id = params['webhook_id']
        domain_id = params['domain_id']
        webhook_vo = self.webhook_mgr.get_webhook(webhook_id, domain_id)

        return self.webhook_mgr.update_webhook_by_vo({'state': 'DISABLED'}, webhook_vo)

    @transaction(append_meta={'authorization.scope': 'PROJECT'})
    @check_required(['webhook_id', 'domain_id'])
    def delete(self, params):
        """Delete webhook

        Args:
            params (dict): {
                'webhook_id': 'str',
                'domain_id': 'str'
            }

        Returns:
            None
        """

        self.webhook_mgr.delete_webhook(params['webhook_id'], params['domain_id'])

    @transaction(append_meta={'authorization.scope': 'PROJECT'})
    @check_required(['webhook_id', 'domain_id'])
    def verify_plugin(self, params):
        """ Verify webhook plugin

        Args:
            params (dict): {
                'webhook_id': 'str',
                'domain_id': 'str'
            }

        Returns:
            webhook_vo (object)
        """

        webhook_id = params['webhook_id']
        domain_id = params['domain_id']
        webhook_vo = self.webhook_mgr.get_webhook(webhook_id, domain_id)

        endpoint = self.webhook_plugin_mgr.get_webhook_plugin_endpoint_by_vo(webhook_vo)

        self._verify_plugin(endpoint, webhook_vo.plugin_info.options)

    @transaction(append_meta={'authorization.scope': 'PROJECT'})
    @check_required(['webhook_id', 'domain_id'])
    def update_plugin(self, params):
        """Update webhook plugin

        Args:
            params (dict): {
                'webhook_id': 'str',
                'version': 'str',
                'options': 'dict',
                'upgrade_mode': 'str',
                'domain_id': 'str'
            }

        Returns:
            webhook_vo (object)
        """

        webhook_id = params['webhook_id']
        domain_id = params['domain_id']
        options = params.get('options')
        version = params.get('version')
        upgrade_mode = params.get('upgrade_mode')

        webhook_vo = self.webhook_mgr.get_webhook(webhook_id, domain_id)
        plugin_info = webhook_vo.plugin_info.to_dict()

        if version:
            plugin_info['version'] = version

        if options:
            plugin_info['options'] = options

        if upgrade_mode:
            plugin_info['upgrade_mode'] = upgrade_mode

        endpoint, updated_version = self.webhook_plugin_mgr.get_webhook_plugin_endpoint(plugin_info, domain_id)
        if updated_version:
            plugin_info['version'] = updated_version

        plugin_metadata = self._init_plugin(endpoint, plugin_info.get('options', {}))
        plugin_info['metadata'] = plugin_metadata

        params = {
            'plugin_info': plugin_info
        }

        _LOGGER.debug(f'[update_plugin] {plugin_info}')

        return self.webhook_mgr.update_webhook_by_vo(params, webhook_vo)

    @transaction(append_meta={'authorization.scope': 'PROJECT'})
    @check_required(['webhook_id', 'domain_id'])
    def get(self, params):
        """ Get webhook

        Args:
            params (dict): {
                'webhook_id': 'str',
                'domain_id': 'str',
                'only': 'list
            }

        Returns:
            webhook_vo (object)
        """

        return self.webhook_mgr.get_webhook(params['webhook_id'], params['domain_id'], params.get('only'))

    @transaction(append_meta={'authorization.scope': 'PROJECT'})
    @check_required(['domain_id'])
    @append_query_filter(['webhook_id', 'name', 'state', 'access_key', 'project_id', 'domain_id', 'user_projects'])
    @append_keyword_filter(['webhook_id', 'name'])
    def list(self, params):
        """ List webhooks

        Args:
            params (dict): {
                'webhook_id': 'str',
                'name': 'str',
                'state': 'str',
                'project_id': 'str',
                'domain_id': 'str',
                'query': 'dict (spaceone.api.core.v1.Query)',
                'user_projects': 'list', // from meta
            }

        Returns:
            webhook_vos (object)
            total_count
        """

        query = params.get('query', {})
        return self.webhook_mgr.list_webhooks(query)

    @transaction(append_meta={'authorization.scope': 'PROJECT'})
    @check_required(['query', 'domain_id'])
    @append_query_filter(['domain_id', 'user_projects'])
    @append_keyword_filter(['webhook_id', 'name'])
    def stat(self, params):
        """
        Args:
            params (dict): {
                'domain_id': 'str',
                'query': 'dict (spaceone.api.core.v1.StatisticsQuery)',
                'user_projects': 'list', // from meta
            }

        Returns:
            values (list) : 'list of statistics data'

        """

        query = params.get('query', {})
        return self.webhook_mgr.stat_webhooks(query)

    @staticmethod
    def _generate_access_key():
        return utils.random_string(16)

    @staticmethod
    def _make_webhook_url(webhook_id, access_key):
        return f'/monitoring/v1/webhook/{webhook_id}/{access_key}/events'

    @staticmethod
    def _check_plugin_info(plugin_info_params):
        if 'plugin_id' not in plugin_info_params:
            raise ERROR_REQUIRED_PARAMETER(key='plugin_info.plugin_id')

    def _get_plugin(self, plugin_info, domain_id):
        plugin_id = plugin_info['plugin_id']

        repo_mgr: RepositoryManager = self.locator.get_manager('RepositoryManager')
        plugin_info = repo_mgr.get_plugin(plugin_id, domain_id)

        return plugin_info

    def _init_plugin(self, endpoint, options):
        self.webhook_plugin_mgr.initialize(endpoint)
        return self.webhook_plugin_mgr.init_plugin(options)

    def _verify_plugin(self, endpoint, options):
        self.webhook_plugin_mgr.initialize(endpoint)
        self.webhook_plugin_mgr.verify_plugin(options)
