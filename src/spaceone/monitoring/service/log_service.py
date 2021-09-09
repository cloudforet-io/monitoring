import logging
import traceback
from spaceone.core.service import *

from spaceone.monitoring.error import *
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
    @check_required(['data_source_id', 'resource_type', 'resource_id', 'domain_id'])
    def list(self, params):
        """ Get resource's logs

        Args:
            params (dict): {
                'data_source_id': 'str',
                'resource_type': 'str',
                'resource_id': 'str',
                'filter': 'dict',
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
        resource_type = params['resource_type']
        resource_id = params['resource_id']
        domain_id = params['domain_id']

        data_source_vo = self.data_source_mgr.get_data_source(data_source_id, domain_id)

        self._check_data_source_state(data_source_vo)

        plugin_metadata = data_source_vo.plugin_info.metadata
        plugin_options = data_source_vo.plugin_info.options

        self._check_resource_type(plugin_metadata, resource_type)

        data_source_dict = data_source_vo.to_dict()
        plugin_info = data_source_dict['plugin_info']

        self.ds_plugin_mgr.initialize(plugin_info, domain_id)

        plugin_filter = {}

        resource_mgr = self._get_resource_manager(resource_type)
        resource_info = resource_mgr.get_resource(resource_type, resource_id, domain_id)

        secret_data, schema = self._get_secret_data(resource_id, resource_type, resource_info, data_source_vo, domain_id)

        logs_info = self.ds_plugin_mgr.list_logs(schema, plugin_options, secret_data, resource_info, plugin_filter,
                                                 params.get('start'), params.get('end'), params.get('sort', {}),
                                                 params.get('limit', 100))

        return {
            'logs': logs_info['logs'],
            'domain_id': domain_id
        }

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
            return self.secret_mgr.get_resource_secret_data(resource_id, secret_filter, domain_id)

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
