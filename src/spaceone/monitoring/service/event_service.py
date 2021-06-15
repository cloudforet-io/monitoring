import logging

from spaceone.core.service import *
from spaceone.core import cache
from spaceone.monitoring.error.webhook import *
from spaceone.monitoring.model.event_model import Event
from spaceone.monitoring.model.webhook_model import Webhook
from spaceone.monitoring.manager.alert_manager import AlertManager
from spaceone.monitoring.manager.webhook_manager import WebhookManager
from spaceone.monitoring.manager.event_manager import EventManager
from spaceone.monitoring.manager.webhook_plugin_manager import WebhookPluginManager

_LOGGER = logging.getLogger(__name__)


@authentication_handler
@authorization_handler
@mutation_handler
@event_handler
class EventService(BaseService):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.event_mgr: EventManager = self.locator.get_manager('EventManager')

    @transaction(append_meta={'authorization.scope': 'PROJECT'})
    @check_required(['webhook_id', 'access_key', 'data'])
    def create(self, params):
        """Create event

        Args:
            params (dict): {
                'webhook_id': 'str',
                'access_key': 'str',
                'data': 'str'
            }

        Returns:
            event_vo (object)
        """

        webhook_vo = self._check_access_key(params['access_key'], params['webhook_id'])

        self._check_webhook_state(webhook_vo)

        plugin_id = webhook_vo.plugin_info.plugin_id
        version = webhook_vo.plugin_info.version

        return self.event_mgr.create_event(params)

    @transaction(append_meta={'authorization.scope': 'PROJECT'})
    @check_required(['event_id', 'domain_id'])
    def get(self, params):
        """ Get event

        Args:
            params (dict): {
                'event_id': 'str',
                'domain_id': 'str',
                'only': 'list
            }

        Returns:
            event_vo (object)
        """

        return self.event_mgr.get_event(params['event_id'], params['domain_id'], params.get('only'))

    @transaction(append_meta={
        'authorization.scope': 'PROJECT',
        'mutation.append_parameter': {'user_projects': 'authorization.projects'}
    })
    @check_required(['domain_id'])
    @append_query_filter(['event_id', 'event_key', 'event_type', 'severity', 'resource_id', 'alert_id',
                          'webhook_id', 'project_id', 'domain_id', 'user_projects'])
    @append_keyword_filter(['event_id', 'title'])
    def list(self, params):
        """ List events

        Args:
            params (dict): {
                'event_id': 'str',
                'event_key': 'str',
                'event_type': 'str',
                'severity': 'str',
                'resource_id': 'str',
                'alert_id': 'str',
                'webhook_id': 'str',
                'project_id': 'str',
                'domain_id': 'str',
                'query': 'dict (spaceone.api.core.v1.Query)',
                'user_projects': 'list', // from meta
            }

        Returns:
            event_vos (object)
            total_count
        """

        query = params.get('query', {})
        return self.event_mgr.list_events(query)

    @transaction(append_meta={
        'authorization.scope': 'PROJECT',
        'mutation.append_parameter': {'user_projects': 'authorization.projects'}
    })
    @check_required(['query', 'domain_id'])
    @append_query_filter(['domain_id', 'user_projects'])
    @append_keyword_filter(['event_id', 'title'])
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
        return self.event_mgr.stat_events(query)

    @cache.cacheable(key='webhook:access-key:{request_access_key}:{webhook_id}', expire=86400)
    def _check_access_key(self, request_access_key, webhook_id):
        webhook_mgr: WebhookManager = self.locator.get_manager('Webhook')
        webhook_vo: Webhook = webhook_mgr.get_webhook_by_id(webhook_id)

        if request_access_key != webhook_vo.access_key:
            raise ERROR_PERMISSION_DENIED()

        return webhook_vo

    @staticmethod
    def _check_webhook_state(webhook_vo):
        if webhook_vo.state == 'DISABLED':
            raise ERROR_WEBHOOK_STATE_DISABLED(webhook_id=webhook_vo.webhook_id)
