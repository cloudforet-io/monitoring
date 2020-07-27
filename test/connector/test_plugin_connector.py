import unittest
import os
from unittest.mock import patch

from spaceone.core.unittest.result import print_data
from spaceone.core.unittest.runner import RichTestRunner
from spaceone.core import config
from spaceone.core import utils
from spaceone.core.transaction import Transaction
from spaceone.monitoring.connector.plugin_connector import PluginConnector
from spaceone.monitoring.error import *


class TestPluginConnector(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        config.init_conf(package='spaceone.monitoring')
        config_path = os.environ.get('TEST_CONFIG')
        test_config = utils.load_yaml_from_file(config_path)

        cls.transaction = Transaction({
            'token': test_config.get('access_token')
        })

        cls.domain_id = test_config.get('domain_id')
        cls.connector_conf = test_config.get('PluginConnector')
        cls.plugin_connector = PluginConnector(cls.transaction, cls.connector_conf)
        super().setUpClass()

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()

    def test_get_plugin_endpoint(self):
        plugin_id = self.connector_conf['plugin_id']
        version = self.connector_conf['version']
        response = self.plugin_connector.get_plugin_endpoint(plugin_id, version, self.domain_id)
        print_data(response, 'test_get_plugin_endpoint')


if __name__ == "__main__":
    unittest.main(testRunner=RichTestRunner)
