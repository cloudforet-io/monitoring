import logging

from spaceone.core.service import *
from spaceone.core.utils import get_dict_value

from spaceone.monitoring.error import *
from spaceone.monitoring.conf.log_conf import *
from spaceone.monitoring.manager.identity_manager import IdentityManager
from spaceone.monitoring.manager.inventory_manager import InventoryManager
from spaceone.monitoring.manager.secret_manager import SecretManager
from spaceone.monitoring.manager.data_source_manager import DataSourceManager
from spaceone.monitoring.manager.data_source_plugin_manager import DataSourcePluginManager

_LOGGER = logging.getLogger(__name__)


@authentication_handler
@authorization_handler
@mutation_handler
@event_handler
class LogService(BaseService):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.identity_mgr: IdentityManager = self.locator.get_manager('IdentityManager')
        self.inventory_mgr: InventoryManager = self.locator.get_manager('InventoryManager')
        self.secret_mgr: SecretManager = self.locator.get_manager('SecretManager')
        self.data_source_mgr: DataSourceManager = self.locator.get_manager('DataSourceManager')
        self.ds_plugin_mgr: DataSourcePluginManager = self.locator.get_manager('DataSourcePluginManager')

    @transaction(append_meta={'authorization.scope': 'DOMAIN'})
    @check_required(['data_source_id', 'resource_id', 'domain_id'])
    def list(self, params):
        """ Get resource's logs

        Args:
            params (dict): {
                'data_source_id': 'str',
                'resource_id': 'str',
                'keyword': 'str',
                'start': 'datetime',
                'end': 'datetime',
                'sort': 'dict',
                'limit': 'int',
                'domain_id': 'str'
            }

        Returns:
            logs (list)
        """
        data_source_id = params['data_source_id']
        resource_id = params['resource_id']
        domain_id = params['domain_id']

        data_source_vo = self.data_source_mgr.get_data_source(data_source_id, domain_id)
        self._check_data_source_state(data_source_vo)
        self.plugin_initialize(data_source_vo)

        plugin_options = data_source_vo.plugin_info.options
        cloud_service_info = self.inventory_mgr.get_cloud_service(resource_id, domain_id)
        query = self.get_query_from_cloud_service(cloud_service_info)
        secret = self.secret_mgr.get_secret_from_resource(cloud_service_info, data_source_vo, domain_id)
        secret_data = self.secret_mgr.get_secret_data(secret['secret_id'], domain_id)

        logs_info = self.ds_plugin_mgr.list_logs(secret.get('schema'), plugin_options, secret_data, query,
                                                 params.get('start'), params.get('end'),
                                                 params.get('sort', {}), params.get('limit', LOG_LIMIT))

        return {
            'logs': logs_info['logs'],
            'domain_id': domain_id
        }

    def plugin_initialize(self, data_source_vo):
        endpoint = self.ds_plugin_mgr.get_data_source_plugin_endpoint_by_vo(data_source_vo)
        self.ds_plugin_mgr.initialize(endpoint)

    @staticmethod
    def get_query_from_cloud_service(cloud_service_info):
        query_key = QUERY_KEY_MAP.get(cloud_service_info['provider'], '')
        return get_dict_value(cloud_service_info, query_key, default_value={})

    @staticmethod
    def _check_data_source_state(data_source_vo):
        if data_source_vo.state == 'DISABLED':
            raise ERROR_DATA_SOURCE_STATE_DISABLED(data_source_id=data_source_vo.data_source_id)

    @staticmethod
    def _check_resource_type(plugin_metadata, resource_type):
        supported_resource_type = plugin_metadata['supported_resource_type']

        if resource_type not in supported_resource_type:
            raise ERROR_NOT_SUPPORT_RESOURCE_TYPE(supported_resource_type=supported_resource_type)

    def _get_resource_manager(self, resource_type):
        service, resource = resource_type.split('.')
        if service == 'identity':
            return self.identity_mgr
        else:
            return self.inventory_mgr

    def _get_secret_data(self, resource_id, resource_type, resource_info, data_source_vo, domain_id):
        use_resource_secret = data_source_vo.capability.get('use_resource_secret', False)
        supported_schema = data_source_vo.capability.get('supported_schema', [])

        if use_resource_secret:
            secret_filter = {
                'provider': data_source_vo.plugin_info['provider'],
                'supported_schema': supported_schema
            }
            secret_filter.update(self._get_secret_extra_filter(resource_type, resource_id, resource_info))
            return self.secret_mgr.get_resource_secret_data(secret_filter, domain_id, resource_id=resource_id)

        else:
            secret_filter = {
                'secret_id': data_source_vo.plugin_info['secret_id'],
                'supported_schema': supported_schema
            }
            return self.secret_mgr.get_plugin_secret_data(secret_filter, domain_id)

    @staticmethod
    def _get_secret_extra_filter(resource_type, resource_id, resource_info):
        service, resource = resource_type.split('.')

        if service == 'identity':
            if resource == 'Project':
                return {'project_id': resource_id}
            elif resource == 'ServiceAccount':
                return {'service_account_id': resource_id}
            else:
                return {}
        else:
            return {'secrets': resource_info['collection_info']['secrets']}
