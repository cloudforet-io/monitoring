import unittest
import os
from unittest.mock import patch

from spaceone.core.unittest.result import print_data
from spaceone.core.unittest.runner import RichTestRunner
from spaceone.core import config
from spaceone.core import utils
from spaceone.core.transaction import Transaction
from spaceone.monitoring.connector.inventory_connector import InventoryConnector
from spaceone.monitoring.error import *


class TestInventoryConnector(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        config.init_conf(package='spaceone.monitoring')
        config.set_service_config()
        config.set_global(MOCK_MODE=True)
        config_path = os.environ.get('TEST_CONFIG')
        test_config = utils.load_yaml_from_file(config_path)

        cls.transaction = Transaction({
            'token': test_config.get('access_token')
        })

        cls.domain_id = test_config.get('domain_id')
        cls.connector_conf = test_config.get('InventoryConnector')
        cls.inventory_connector = InventoryConnector(cls.transaction, cls.connector_conf)
        super().setUpClass()

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()

    def test_list_servers(self):
        response = self.inventory_connector.list_servers({'page': {'limit': 3}, 'minimal': True}, self.domain_id)
        server_ids = [server_info['server_id'] for server_info in response['results']]

        query = {
            'filter': [{
                'k': 'server_id',
                'v': server_ids,
                'o': 'in'
            }],
            'only': ['server_id', 'name', 'collection_info.secrets']
        }
        response = self.inventory_connector.list_servers(query, self.domain_id)
        print_data(response, 'test_list_servers')

    def test_list_cloud_services(self):
        response = self.inventory_connector.list_cloud_services({'page': {'limit': 3}, 'minimal': True}, self.domain_id)
        cloud_service_ids = [cloud_service_info['cloud_service_id'] for cloud_service_info in response['results']]

        query = {
            'filter': [{
                'k': 'cloud_service_id',
                'v': cloud_service_ids,
                'o': 'in'
            }],
            'only': ['cloud_service_id', 'reference.resource_id', 'collection_info.secrets']
        }
        response = self.inventory_connector.list_cloud_services(query, self.domain_id)
        print_data(response, 'test_list_cloud_services')


if __name__ == "__main__":
    unittest.main(testRunner=RichTestRunner)
