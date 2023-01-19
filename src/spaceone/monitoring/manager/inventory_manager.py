import logging

from spaceone.core.manager import BaseManager
from spaceone.core.connector.space_connector import SpaceConnector
from spaceone.monitoring.error import *

_LOGGER = logging.getLogger(__name__)


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
        return self.get_cloud_service(resource_id, domain_id)

    def list_resources(self, resources, required_keys, domain_id):
        query = self._make_query(resources, required_keys)
        response = self.list_cloud_services(query, domain_id)
        return response.get('results', [])

    @staticmethod
    def _make_query(resources, required_keys):
        only_keys = list(set(['cloud_service_id', 'collection_info.secret_id', 'region_code'] + required_keys))
        only_keys.sort()

        return {
            'filter': [{
                'k': 'cloud_service_id',
                'v': resources,
                'o': 'in'
            }],
            'only': only_keys
        }
