import unittest
import os
from unittest.mock import patch

from spaceone.core.unittest.result import print_data
from spaceone.core.unittest.runner import RichTestRunner
from spaceone.core import config
from spaceone.core import utils
from spaceone.core.transaction import Transaction
from spaceone.monitoring.connector.repository_connector import RepositoryConnector
from spaceone.monitoring.error import *


class TestRepositoryConnector(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        config.init_conf(service='monitoring')
        config_path = os.environ.get('TEST_CONFIG')
        test_config = utils.load_yaml_from_file(config_path)

        cls.transaction = Transaction({
            'token': test_config.get('access_token')
        })

        cls.domain_id = test_config.get('domain_id')
        cls.connector_conf = test_config.get('RepositoryConnector')
        cls.repo_connector = RepositoryConnector(cls.transaction, cls.connector_conf)
        super().setUpClass()

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()

    def test_get_plugin(self):
        plugin_id = self.connector_conf['plugin_id']

        response = self.repo_connector.get_plugin(plugin_id, self.domain_id)
        print_data(response, 'test_get_plugin')

    def test_get_plugin_versions(self):
        plugin_id = self.connector_conf['plugin_id']

        response = self.repo_connector.get_plugin_versions(plugin_id, self.domain_id)
        print_data(response, 'test_get_plugin_versions')

if __name__ == "__main__":
    unittest.main(testRunner=RichTestRunner)
