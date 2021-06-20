import logging

from spaceone.core.manager import BaseManager
from spaceone.core.connector.space_connector import SpaceConnector
from spaceone.monitoring.error import *

_LOGGER = logging.getLogger(__name__)
_RESOURCE_KEYS = {
    'inventory.Server': 'server_id',
    'inventory.CloudService': 'cloud_service_id'
}


class InventoryManager(BaseManager):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.inventory_connector: SpaceConnector = self.locator.get_connector('SpaceConnector', service='inventory')

    def get_server(self, server_id, domain_id):
        return self.inventory_connector.dispatch('Server.get', {'server_id': server_id, 'domain_id': domain_id})

    def list_servers(self, query, domain_id):
        return self.inventory_connector.dispatch('Server.list', {'query': query, 'domain_id': domain_id})

    def get_cloud_service(self, cloud_service_id, domain_id):
        return self.inventory_connector.dispatch('CloudService.get', {'cloud_service_id': cloud_service_id,
                                                                      'domain_id': domain_id})

    def list_cloud_services(self, query, domain_id):
        return self.inventory_connector.dispatch('CloudService.list', {'query': query, 'domain_id': domain_id})

    def get_resource(self, resource_type, resource_id, domain_id):
        if resource_type == 'inventory.Server':
            return self.get_server(resource_id, domain_id)
        elif resource_type == 'inventory.CloudService':
            return self.get_cloud_service(resource_id, domain_id)

    def list_resources(self, resource_type, resources, required_keys, domain_id):
        query = self._make_query(resource_type, resources, required_keys)

        if resource_type == 'inventory.Server':
            response = self.list_servers(query, domain_id)
        elif resource_type == 'inventory.CloudService':
            response = self.list_cloud_services(query, domain_id)
        else:
            response = {
                'total_count': 0,
                'results': []
            }

        if response.get('total_count', 0) == 0:
            raise ERROR_NOT_FOUND(key='resources', value=resources)

        return self._change_resources_info(resource_type, response)

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
