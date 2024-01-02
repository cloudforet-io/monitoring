import datetime
import logging

from spaceone.core.service import *
from spaceone.core.utils import get_dict_value

from spaceone.monitoring.error import *
from spaceone.monitoring.manager import PluginManager
from spaceone.monitoring.manager.data_source_manager import DataSourceManager
from spaceone.monitoring.manager.data_source_plugin_manager import (
    DataSourcePluginManager,
)
from spaceone.monitoring.manager.identity_manager import IdentityManager
from spaceone.monitoring.manager.inventory_manager import InventoryManager
from spaceone.monitoring.manager.secret_manager import SecretManager

_LOGGER = logging.getLogger(__name__)


@authentication_handler
@authorization_handler
@mutation_handler
@event_handler
class LogService(BaseService):
    resource = "Log"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.identity_mgr: IdentityManager = self.locator.get_manager("IdentityManager")
        self.inventory_mgr: InventoryManager = self.locator.get_manager(
            "InventoryManager"
        )
        self.secret_mgr: SecretManager = self.locator.get_manager("SecretManager")
        self.data_source_mgr: DataSourceManager = self.locator.get_manager(
            "DataSourceManager"
        )
        self.ds_plugin_mgr: DataSourcePluginManager = self.locator.get_manager(
            "DataSourcePluginManager"
        )

    @transaction(
        permission="monitoring:Log.read",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @check_required(["data_source_id", "resource_id", "start", "domain_id"])
    def list(self, params):
        """Get resource's logs

        Args:
            params (dict): {
                'data_source_id': 'str',   # required
                'resource_id': 'str',      # required
                'keyword': 'str',
                'start': 'datetime',       # required
                'end': 'datetime',         # default
                'sort': 'dict',
                'limit': 'int',
                'domain_id': 'str'
            }

        Returns:
            logs (list)
        """
        data_source_id = params["data_source_id"]
        resource_id = params["resource_id"]
        start = params["start"]
        end = params.get("end", str(datetime.datetime.now()))
        domain_id = params["domain_id"]
        secret_data = {}

        data_source_vo = self.data_source_mgr.get_data_source(data_source_id, domain_id)
        self._check_data_source_state(data_source_vo)
        plugin_info = data_source_vo.plugin_info.to_dict()
        plugin_mgr: PluginManager = self.locator.get_manager(PluginManager)
        endpoint, updated_version = plugin_mgr.get_plugin_endpoint(
            plugin_info, data_source_vo.domain_id
        )

        if updated_version:
            _LOGGER.debug(
                f'[get_data_source_plugin_endpoint_by_vo] upgrade plugin version: {plugin_info["version"]} -> {updated_version}'
            )
            plugin_info = data_source_vo.plugin_info.to_dict()
            plugin_metadata = self.ds_plugin_mgr.init_plugin(
                endpoint, plugin_info.get("options", {}), data_source_vo.monitoring_type
            )
            plugin_info["version"] = updated_version
            plugin_info["metadata"] = plugin_metadata
            self.data_source_mgr.update_data_source_by_vo(
                {"plugin_info": plugin_info}, data_source_vo
            )

        plugin_options = data_source_vo.plugin_info.options
        cloud_service_info = self.inventory_mgr.get_cloud_service(resource_id)
        query = self.get_query_from_cloud_service(
            cloud_service_info, data_source_vo.plugin_info
        )
        secret = self.secret_mgr.get_secret_from_resource(
            cloud_service_info, data_source_vo
        )
        secret_data = self.secret_mgr.get_secret_data(
            secret.get("secret_id", ""), domain_id
        )

        logs_info = self.ds_plugin_mgr.list_logs(
            endpoint,
            secret.get("schema"),
            plugin_options,
            secret_data,
            query,
            params.get("keyword"),
            start,
            end,
            params.get("sort"),
            params.get("limit"),
        )

        return {"results": logs_info["results"], "domain_id": domain_id}

    @staticmethod
    def get_query_from_cloud_service(cloud_service_info, plugin_info):
        metadata = plugin_info.metadata
        required_keys = metadata.get("required_keys", [])

        if required_keys:
            query_key = required_keys[0]
            query = get_dict_value(cloud_service_info, query_key, default_value={})
            if query:
                return query
            else:
                raise ERROR_REQUIRED_KEYS_NOT_EXISTS(plugin_id=plugin_info.plugin_id)
        else:
            raise ERROR_REQUIRED_KEYS_NOT_EXISTS(plugin_id=plugin_info.plugin_id)

    @staticmethod
    def _check_data_source_state(data_source_vo):
        if data_source_vo.state == "DISABLED":
            raise ERROR_DATA_SOURCE_STATE_DISABLED(
                data_source_id=data_source_vo.data_source_id
            )
