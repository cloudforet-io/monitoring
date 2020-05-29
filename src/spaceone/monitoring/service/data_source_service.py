import logging

from spaceone.core.service import *

from spaceone.monitoring.error import *
from spaceone.monitoring.manager.repository_manager import RepositoryManager
from spaceone.monitoring.manager.secret_manager import SecretManager
from spaceone.monitoring.manager.plugin_manager import PluginManager
from spaceone.monitoring.manager.data_source_manager import DataSourceManager

_LOGGER = logging.getLogger(__name__)


@authentication_handler
@authorization_handler
@event_handler
class DataSourceService(BaseService):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data_source_mgr: DataSourceManager = self.locator.get_manager('DataSourceManager')

    @transaction
    @check_required(['name', 'plugin_info', 'domain_id'])
    def register(self, params):
        """Register data source

        Args:
            params (dict): {
                'name': 'str',
                'monitoring_type': 'str',
                'plugin_info': 'dict',
                'tags': 'dict',
                'domain_id': 'str'
            }

        Returns:
            data_source_vo (object)
        """
        domain_id = params['domain_id']

        self._check_plugin_info(params['plugin_info'])
        plugin_info = self._get_plugin(params['plugin_info'], domain_id)
        params['capability'] = plugin_info.get('capability', {})
        params['provider'] = plugin_info.get('provider')

        self._check_plugin_capability(params['capability'])
        params['monitoring_type'] = params['capability']['monitoring_type']

        verified_options = self._verify_plugin(params['plugin_info'], params['capability'], domain_id)
        params['plugin_info']['options'].update(verified_options)

        return self.data_source_mgr.register_data_source(params)

    @transaction
    @check_required(['data_source_id', 'domain_id'])
    def update(self, params):
        """Update data source

        Args:
            params (dict): {
                'data_source_id': 'str',
                'name': 'dict',
                'plugin_info': 'dict',
                'tags': 'dict'
                'domain_id': 'str'
            }

        Returns:
            data_source_vo (object)
        """
        data_source_id = params['data_source_id']
        domain_id = params['domain_id']
        data_source_vo = self.data_source_mgr.get_data_source(data_source_id, domain_id)

        if 'plugin_info' in params:
            self._check_plugin_info(params['plugin_info'])

            if params['plugin_info']['plugin_id'] != data_source_vo.plugin_info.plugin_id:
                raise ERROR_NOT_ALLOWED_PLUGIN_ID(old_plugin_id=data_source_vo.plugin_info.plugin_id,
                                                  new_plugin_id=params['plugin_info']['plugin_id'])

            verified_options = self._verify_plugin(params['plugin_info'],
                                                   data_source_vo.capability, domain_id)

            params['plugin_info']['options'].update(verified_options)

        return self.data_source_mgr.update_data_source_by_vo(params, data_source_vo)

    @transaction
    @check_required(['data_source_id', 'domain_id'])
    def enable(self, params):
        """ Enable data source

        Args:
            params (dict): {
                'data_source_id': 'str',
                'domain_id': 'str'
            }

        Returns:
            data_source_vo (object)
        """

        data_source_id = params['data_source_id']
        domain_id = params['domain_id']
        data_source_vo = self.data_source_mgr.get_data_source(data_source_id, domain_id)

        return self.data_source_mgr.update_data_source_by_vo({'state': 'ENABLED'},
                                                             data_source_vo)

    @transaction
    @check_required(['data_source_id', 'domain_id'])
    def disable(self, params):
        """ Disable data source

        Args:
            params (dict): {
                'data_source_id': 'str',
                'domain_id': 'str'
            }

        Returns:
            data_source_vo (object)
        """

        data_source_id = params['data_source_id']
        domain_id = params['domain_id']
        data_source_vo = self.data_source_mgr.get_data_source(data_source_id, domain_id)

        return self.data_source_mgr.update_data_source_by_vo({'state': 'DISABLED'},
                                                             data_source_vo)

    @transaction
    @check_required(['data_source_id', 'domain_id'])
    def deregister(self, params):
        """Deregister data source

        Args:
            params (dict): {
                'data_source_id': 'str',
                'domain_id': 'str'
            }

        Returns:
            None
        """

        self.data_source_mgr.deregister_data_source(params['data_source_id'], params['domain_id'])

    @transaction
    @check_required(['data_source_id', 'domain_id'])
    def verify_plugin(self, params):
        """ Verify data source plugin

        Args:
            params (dict): {
                'data_source_id': 'str',
                'domain_id': 'str'
            }

        Returns:
            data_source_vo (object)
        """

        data_source_id = params['data_source_id']
        domain_id = params['domain_id']
        data_source_vo = self.data_source_mgr.get_data_source(data_source_id, domain_id)

        self._verify_plugin(data_source_vo.plugin_info, data_source_vo.capability, domain_id)

        return {'status': True}

    @transaction
    @check_required(['data_source_id', 'domain_id'])
    def get(self, params):
        """ Get data source

        Args:
            params (dict): {
                'data_source_id': 'str',
                'domain_id': 'str',
                'only': 'list
            }

        Returns:
            data_source_vo (object)
        """
        return self.data_source_mgr.get_data_source(params['data_source_id'], params['domain_id'], params.get('only'))

    @transaction
    @check_required(['domain_id'])
    @append_query_filter(['data_source_id', 'name', 'state', 'monitoring_type', 'provider', 'domain_id'])
    @append_keyword_filter(['data_source_id', 'name', 'provider'])
    def list(self, params):
        """ List data sources

        Args:
            params (dict): {
                'data_source_id': 'str',
                'name': 'str',
                'state': 'str',
                'monitoring_type': 'str',
                'provider': 'str',
                'domain_id': 'str',
                'query': 'dict (spaceone.api.core.v1.Query)'
            }

        Returns:
            data_source_vos (object)
            total_count
        """

        query = params.get('query', {})
        return self.data_source_mgr.list_data_sources(query)

    @transaction
    @check_required(['query', 'domain_id'])
    @append_query_filter(['domain_id'])
    def stat(self, params):
        """
        Args:
            params (dict): {
                'domain_id': 'str',
                'query': 'dict (spaceone.api.core.v1.StatisticsQuery)'
            }

        Returns:
            values (list) : 'list of statistics data'

        """

        query = params.get('query', {})
        return self.data_source_mgr.stat_data_sources(query)

    @staticmethod
    def _check_plugin_capability(capability):
        if 'monitoring_type' not in capability:
            raise ERROR_WRONG_PLUGIN_SETTINGS(key='capability.monitoring_type')
        else:
            if capability['monitoring_type'] not in ['METRIC', 'LOG']:
                raise ERROR_WRONG_PLUGIN_SETTINGS(key='capability.monitoring_type')

        if 'supported_schema' not in capability:
            raise ERROR_WRONG_PLUGIN_SETTINGS(key='capability.supported_schema')

    @staticmethod
    def _check_plugin_info(plugin_info_params):
        if 'plugin_id' not in plugin_info_params:
            raise ERROR_REQUIRED_PARAMETER(key='plugin_info.plugin_id')

        if 'version' not in plugin_info_params:
            raise ERROR_REQUIRED_PARAMETER(key='plugin_info.version')

        if 'options' not in plugin_info_params:
            raise ERROR_REQUIRED_PARAMETER(key='plugin_info.options')

        secret_id = plugin_info_params.get('secret_id')
        provider = plugin_info_params.get('provider')

        if secret_id is None and provider is None:
            raise ERROR_REQUIRED_PARAMETER(key='plugin_info.[secret_id | provider]')

    def _get_plugin(self, plugin_info, domain_id):
        plugin_id = plugin_info['plugin_id']
        version = plugin_info['version']

        repo_mgr: RepositoryManager = self.locator.get_manager('RepositoryManager')
        plugin_info = repo_mgr.get_plugin(plugin_id, domain_id)
        repo_mgr.check_plugin_version(plugin_id, version, domain_id)

        return plugin_info

    def _verify_plugin(self, plugin_info, capability, domain_id):
        plugin_id = plugin_info['plugin_id']
        version = plugin_info['version']
        options = plugin_info['options']
        secret_id = plugin_info.get('secret_id')
        provider = plugin_info.get('provider')
        monitoring_type = capability['monitoring_type']

        secret_mgr: SecretManager = self.locator.get_manager('SecretManager')
        secret_data = secret_mgr.get_plugin_secret(plugin_id, secret_id, provider, capability, domain_id)

        plugin_mgr: PluginManager = self.locator.get_manager('PluginManager')
        plugin_mgr.init_plugin(plugin_id, version, domain_id)
        verified_options = plugin_mgr.verify_plugin(options, secret_data, monitoring_type)
        return verified_options
