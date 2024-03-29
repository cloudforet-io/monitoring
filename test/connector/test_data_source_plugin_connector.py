import unittest
import os
from datetime import datetime, timedelta
from unittest.mock import patch

from spaceone.core.unittest.result import print_data
from spaceone.core.unittest.runner import RichTestRunner
from spaceone.core import config
from spaceone.core import utils
from spaceone.core.transaction import Transaction
from spaceone.monitoring.connector.datasource_plugin_connector import (
    DataSourcePluginConnector,
)
from spaceone.monitoring.error import *


class TestMonitoringPluginConnector(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        config.init_conf(package="spaceone.monitoring")
        config.set_service_config()
        config.set_global(MOCK_MODE=True)
        config_path = os.environ.get("TEST_CONFIG")
        test_config = utils.load_yaml_from_file(config_path)

        cls.transaction = Transaction()
        cls.connector_conf = test_config.get("MonitoringPluginConnector", {})
        cls.dsp_connector = DataSourcePluginConnector(cls.transaction, {})
        super().setUpClass()

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()

    def test_verify_plugin_with_secret_data(self):
        endpoint = self.connector_conf["endpoint"]
        secret_data = self.connector_conf["secret_data"]
        schema = self.connector_conf["schema"]

        self.dsp_connector.initialize(endpoint)
        response = self.dsp_connector.verify({}, secret_data, schema)
        print_data(response, "test_verify_plugin_with_secret_data")

    def test_list_metrics(self):
        endpoint = self.connector_conf["endpoint"]
        secret_data = self.connector_conf["secret_data"]
        resource = self.connector_conf["resource"]
        schema = self.connector_conf["schema"]

        self.dsp_connector.initialize(endpoint)
        response = self.dsp_connector.list_metrics(schema, {}, secret_data, resource)
        print_data(response, "test_list_metrics")

    def test_get_metric_data(self):
        endpoint = self.connector_conf["endpoint"]
        secret_data = self.connector_conf["secret_data"]
        resource = self.connector_conf["resource"]
        metric_name = self.connector_conf["metric"]
        schema = self.connector_conf["schema"]

        end = datetime.utcnow()
        start = end - timedelta(minutes=60)

        self.dsp_connector.initialize(endpoint)
        response = self.dsp_connector.get_metric_data(
            schema, {}, secret_data, resource, metric_name, start, end, None, None
        )

        print_data(response, "test_get_metric_data")


if __name__ == "__main__":
    unittest.main(testRunner=RichTestRunner)
