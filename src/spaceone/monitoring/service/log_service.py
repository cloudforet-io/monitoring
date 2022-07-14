import logging
import datetime
from spaceone.core.service import *
from spaceone.core.utils import get_dict_value
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
    @check_required(['data_source_id', 'resource_id', 'start', 'domain_id'])
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
        start = params['start']
        end = params.get('end', str(datetime.datetime.now()))
        domain_id = params['domain_id']

        data_source_vo = self.data_source_mgr.get_data_source(data_source_id, domain_id)
        self._check_data_source_state(data_source_vo)
        self.plugin_initialize(data_source_vo)

        plugin_options = data_source_vo.plugin_info.options
        cloud_service_info = self.inventory_mgr.get_cloud_service(resource_id, domain_id)
        query = self.get_query_from_cloud_service(cloud_service_info, data_source_vo.plugin_info)
        secret = self.secret_mgr.get_secret_from_resource(cloud_service_info, data_source_vo, domain_id)
        secret_data = self.secret_mgr.get_secret_data(secret['secret_id'], domain_id)

        logs_info = self.ds_plugin_mgr.list_logs(secret.get('schema'), plugin_options, secret_data,
                                                 query, params.get('keyword'),
                                                 start, end, params.get('sort'), params.get('limit'))

        return {
            'results': logs_info['results'],
            'domain_id': domain_id
        }

    def plugin_initialize(self, data_source_vo):
        endpoint = self.ds_plugin_mgr.get_data_source_plugin_endpoint_by_vo(data_source_vo)
        self.ds_plugin_mgr.initialize(endpoint)

    @staticmethod
    def get_query_from_cloud_service(cloud_service_info, plugin_info):
        metadata = plugin_info.metadata
        required_keys = metadata.get('required_keys', [])

        if required_keys:
            query_key = required_keys[0]
            return get_dict_value(cloud_service_info, query_key, default_value={})
        else:
            raise ERROR_REQUIRED_KEYS_NOT_EXISTS(plugin_id=plugin_info.plugin_id)

    @staticmethod
    def _check_data_source_state(data_source_vo):
        if data_source_vo.state == 'DISABLED':
            raise ERROR_DATA_SOURCE_STATE_DISABLED(data_source_id=data_source_vo.data_source_id)
