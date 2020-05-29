import unittest
import os
from unittest.mock import patch

from spaceone.core.unittest.result import print_data
from spaceone.core.unittest.runner import RichTestRunner
from spaceone.core import config
from spaceone.core import utils
from spaceone.core.transaction import Transaction
from spaceone.monitoring.connector.identity_connector import IdentityConnector
from spaceone.monitoring.error import *


class TestIdentityConnector(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        config.init_conf(service='monitoring')
        config_path = os.environ.get('TEST_CONFIG')
        test_config = utils.load_yaml_from_file(config_path)

        cls.transaction = Transaction({
            'token': test_config.get('access_token')
        })

        cls.domain_id = test_config.get('domain_id')
        cls.connector_conf = test_config.get('IdentityConnector')
        cls.identity_connector = IdentityConnector(cls.transaction, cls.connector_conf)
        super().setUpClass()

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()

    def test_get_project(self):
        project_id = self.connector_conf['project_id']
        response = self.identity_connector.get_project(project_id, self.domain_id)
        print_data(response, 'test_get_project')

    def test_get_service_account(self):
        service_account_id = self.connector_conf['service_account_id']
        response = self.identity_connector.get_service_account(service_account_id, self.domain_id)
        print_data(response, 'test_get_service_account')


if __name__ == "__main__":
    unittest.main(testRunner=RichTestRunner)
