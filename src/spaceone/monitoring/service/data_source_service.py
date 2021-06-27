import logging

from spaceone.core.service import *
from spaceone.core import utils
from spaceone.monitoring.error import *
from spaceone.monitoring.model.data_source_model import DataSource
from spaceone.monitoring.manager.repository_manager import RepositoryManager
from spaceone.monitoring.manager.secret_manager import SecretManager
from spaceone.monitoring.manager.data_source_plugin_manager import DataSourcePluginManager
from spaceone.monitoring.manager.data_source_manager import DataSourceManager

_LOGGER = logging.getLogger(__name__)


@authentication_handler
@authorization_handler
@mutation_handler
@event_handler
class DataSourceService(BaseService):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data_source_mgr: DataSourceManager = self.locator.get_manager('DataSourceManager')

    @transaction(append_meta={'authorization.scope': 'DOMAIN'})
    @check_required(['name', 'plugin_info', 'domain_id'])
    def register(self, params):
        """Register data source

        Args:
            params (dict): {
                'name': 'str',
                'plugin_info': 'dict',
                'tags': 'dict',
                'domain_id': 'str'
            }

        Returns:
            data_source_vo (object)
        """

        domain_id = params['domain_id']

        if 'tags' in params:
            params['tags'] = utils.dict_to_tags(params['tags'])

        self._check_plugin_info(params['plugin_info'])
        plugin_info = self._get_plugin(params['plugin_info'], domain_id)
        params['capability'] = plugin_info.get('capability', {})
        params['provider'] = plugin_info.get('provider')

        self._check_plugin_capability(params['capability'])
        params['monitoring_type'] = params['capability']['monitoring_type']

        # Update metadata
        plugin_metadata = self._init_plugin(params['plugin_info'], params['monitoring_type'], domain_id)
        params['plugin_info']['metadata'] = plugin_metadata

        return self.data_source_mgr.register_data_source(params)

    @transaction(append_meta={'authorization.scope': 'DOMAIN'})
    @check_required(['data_source_id', 'domain_id'])
    def update(self, params):
        """Update data source

        Args:
            params (dict): {
                'data_source_id': 'str',
                'name': 'dict',
                'tags': 'dict'
                'domain_id': 'str'
            }

        Returns:
            data_source_vo (object)
        """
        data_source_id = params['data_source_id']
        domain_id = params['domain_id']
        data_source_vo = self.data_source_mgr.get_data_source(data_source_id, domain_id)

        if 'tags' in params:
            params['tags'] = utils.dict_to_tags(params['tags'])

        if 'plugin_info' in params:
            self._check_plugin_info(params['plugin_info'])

            if params['plugin_info']['plugin_id'] != data_source_vo.plugin_info.plugin_id:
                raise ERROR_NOT_ALLOWED_PLUGIN_ID(old_plugin_id=data_source_vo.plugin_info.plugin_id,
                                                  new_plugin_id=params['plugin_info']['plugin_id'])

            plugin_metadata = self._init_plugin(params['plugin_info'], data_source_vo.monitoring_type, domain_id)

            # params['plugin_info']['options'].update(plugin_metadata)
            # TODO: Change plugin_info.options to metadata
            params['plugin_info']['metadata'] = plugin_metadata

        return self.data_source_mgr.update_data_source_by_vo(params, data_source_vo)

    @transaction(append_meta={'authorization.scope': 'DOMAIN'})
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

    @transaction(append_meta={'authorization.scope': 'DOMAIN'})
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

    @transaction(append_meta={'authorization.scope': 'DOMAIN'})
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

    @transaction(append_meta={'authorization.scope': 'DOMAIN'})
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

    @transaction(append_meta={'authorization.scope': 'DOMAIN'})
    @check_required(['data_source_id', 'domain_id'])
    def update_plugin(self, params):
        """Update data source plugin

        Args:
            params (dict): {
                'data_source_id': 'str',
                'version': 'str',
                'options': 'dict',
                'domain_id': 'str'
            }

        Returns:
            data_source_vo (object)
        """
        data_source_id = params['data_source_id']
        domain_id = params['domain_id']
        options = params.get('options')
        version = params.get('version')

        data_source_vo = self.data_source_mgr.get_data_source(data_source_id, domain_id)
        data_source_dict = data_source_vo.to_dict()
        plugin_info = data_source_dict['plugin_info']

        if version:
            # Update plugin_version
            plugin_id = plugin_info['plugin_id']
            repo_mgr = self.locator.get_manager('RepositoryManager')
            repo_mgr.check_plugin_version(plugin_id, version, domain_id)

            plugin_info['version'] = version
            metadata = self._init_plugin(data_source_dict['plugin_info'], data_source_vo.monitoring_type, domain_id)
            plugin_info['metadata'] = metadata

        if options or options == {}:
            # Overwriting
            plugin_info['options'] = options

        params = {
            'data_source_id': data_source_id,
            'domain_id': domain_id,
            'plugin_info': plugin_info
        }

        _LOGGER.debug(f'[update_plugin] {plugin_info}')

        return self.data_source_mgr.update_data_source_by_vo(params, data_source_vo)

    @transaction(append_meta={'authorization.scope': 'DOMAIN'})
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

    @transaction(append_meta={'authorization.scope': 'DOMAIN'})
    @check_required(['domain_id'])
    @append_query_filter(['data_source_id', 'name', 'state', 'monitoring_type', 'provider', 'domain_id'])
    @change_tag_filter('tags')
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

    @transaction(append_meta={'authorization.scope': 'DOMAIN'})
    @check_required(['query', 'domain_id'])
    @append_query_filter(['domain_id'])
    @change_tag_filter('tags')
    @append_keyword_filter(['data_source_id', 'name', 'provider'])
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

    def _init_plugin(self, plugin_info, monitoring_type, domain_id):
        plugin_id = plugin_info['plugin_id']
        version = plugin_info['version']
        options = plugin_info['options']

        ds_plugin_mgr: DataSourcePluginManager = self.locator.get_manager('DataSourcePluginManager')
        ds_plugin_mgr.initialize(plugin_id, version, domain_id)
        return ds_plugin_mgr.init_plugin(options, monitoring_type)

    def _verify_plugin(self, plugin_info, capability, domain_id):
        plugin_id = plugin_info['plugin_id']
        version = plugin_info['version']
        options = plugin_info['options']
        secret_id = plugin_info.get('secret_id')
        provider = plugin_info.get('provider')

        secret_mgr: SecretManager = self.locator.get_manager('SecretManager')
        secret_data, schema = secret_mgr.get_plugin_secret(plugin_id, secret_id, provider, capability, domain_id)

        ds_plugin_mgr: DataSourcePluginManager = self.locator.get_manager('DataSourcePluginManager')
        ds_plugin_mgr.initialize(plugin_id, version, domain_id)
        ds_plugin_mgr.verify_plugin(options, secret_data, schema)
