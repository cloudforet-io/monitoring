import unittest
import os
from unittest.mock import patch

from spaceone.core.unittest.result import print_data
from spaceone.core.unittest.runner import RichTestRunner
from spaceone.core import config
from spaceone.core import utils
from spaceone.core.transaction import Transaction
from spaceone.monitoring.connector.secret_connector import SecretConnector
from spaceone.monitoring.error import *


class TestSecretConnector(unittest.TestCase):

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
        cls.connector_conf = test_config.get('SecretConnector')
        cls.secret_connector = SecretConnector(cls.transaction, cls.connector_conf)
        super().setUpClass()

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()

    def test_list_secrets(self):
        query = {
            'filter': []
        }
        response = self.secret_connector.list_secrets(query, self.domain_id)
        print_data(response, 'test_list_secrets')

    def test_get_secret_data(self):
        response = self.secret_connector.list_secrets({}, self.domain_id)
        secret_id = response['results'][0]['secret_id']

        response = self.secret_connector.get_secret_data(secret_id, self.domain_id)
        print_data(response, 'test_get_secret_data')


if __name__ == "__main__":
    unittest.main(testRunner=RichTestRunner)
