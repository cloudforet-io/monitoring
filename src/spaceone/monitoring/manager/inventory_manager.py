import logging

from spaceone.core import utils
from spaceone.core.manager import BaseManager
from spaceone.monitoring.error import *
from spaceone.monitoring.connector.inventory_connector import InventoryConnector
_LOGGER = logging.getLogger(__name__)

_DEFAULT_REFERENCE_KEY = 'reference.resource_id'
_RESOURCE_GET_METHODS = {
    'inventory.Server': 'get_server',
    'inventory.CloudService': 'get_cloud_service',
}
_RESOURCE_LIST_METHODS = {
    'inventory.Server': 'list_servers',
    'inventory.CloudService': 'list_cloud_services',
}
_RESOURCE_KEYS = {
    'inventory.Server': 'server_id',
    'inventory.CloudService': 'cloud_service_id'
}


class InventoryManager(BaseManager):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.inventory_connector: InventoryConnector = self.locator.get_connector('InventoryConnector')

    def get_resource(self, resource_id, resource_type, domain_id):
        get_method = _RESOURCE_GET_METHODS[resource_type]
        return getattr(self.inventory_connector, get_method)(resource_id, domain_id)

    def list_resources(self, resources, resource_type, required_keys, domain_id):
        query = self._make_query(resource_type, resources, required_keys)
        get_method = _RESOURCE_LIST_METHODS[resource_type]

        response = getattr(self.inventory_connector, get_method)(query, domain_id)

        if response.get('total_count', 0) == 0:
            raise ERROR_NOT_FOUND(key='resources', value=resources)

        return self._change_resources_info(resource_type, response)

    def get_resource_key(self, resource_type, resource_info, required_keys):
        reference_key = self._get_reference_key(resource_type, required_keys)
        resource_key = utils.get_dict_value(resource_info, reference_key)

        if resource_key is None:
            raise ERROR_NOT_FOUND_REFERENCE_KEY(reference_keys=str(required_keys))

        return resource_key

    @staticmethod
    def _change_resources_info(resource_type, response):
        resource_key = _RESOURCE_KEYS[resource_type]
        resources_info = {}
        for resource_info in response.get('results', []):
            resource_id = resource_info[resource_key]
            resources_info[resource_id] = resource_info

        return resources_info

    @staticmethod
    def _make_query(resource_type, resources, required_keys):
        resource_key = _RESOURCE_KEYS[resource_type]
        only_keys = list(set([resource_key, 'collection_info.secrets'] + required_keys))
        only_keys.sort()

        return {
            'filter': [{
                'k': resource_key,
                'v': resources,
                'o': 'in'
            }],
            'only': only_keys
        }

    @staticmethod
    def _get_reference_key(resource_type: str, reference_keys: list) -> dict:
        reference_key = _DEFAULT_REFERENCE_KEY

        for key in reference_keys:
            if resource_type == key['resource_type']:
                reference_key = key['reference_key']
                break

        return reference_key
