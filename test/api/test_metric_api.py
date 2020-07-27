import unittest
from unittest.mock import patch
from mongoengine import connect, disconnect
from google.protobuf.json_format import MessageToDict
from google.protobuf.empty_pb2 import Empty

from spaceone.core.unittest.result import print_message
from spaceone.core.unittest.runner import RichTestRunner
from spaceone.core import config
from spaceone.core import utils
from spaceone.core.service import BaseService
from spaceone.core.locator import Locator
from spaceone.core.pygrpc import BaseAPI
from spaceone.api.monitoring.v1 import metric_pb2
from spaceone.monitoring.api.v1.metric import Metric
from test.factory.metric_factory import MetricsFactory, MetricDataFactory


class _MockMetricService(BaseService):

    def get_data(self, params):
        return MetricDataFactory()

    def list(self, params):
        return MetricsFactory()


class TestMetricAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        config.init_conf(package='spaceone.monitoring')
        connect('test', host='mongomock://localhost')
        super().setUpClass()

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        disconnect()

    @patch.object(BaseAPI, '__init__', return_value=None)
    @patch.object(Locator, 'get_service', return_value=_MockMetricService())
    @patch.object(BaseAPI, 'parse_request')
    def test_list_metrics(self, mock_parse_request, *args):
        mock_parse_request.return_value = ({}, {})

        metric_servicer = Metric()
        metrics_info = metric_servicer.list({}, {})

        print_message(metrics_info, 'test_list_metrics')

    @patch.object(BaseAPI, '__init__', return_value=None)
    @patch.object(Locator, 'get_service', return_value=_MockMetricService())
    @patch.object(BaseAPI, 'parse_request')
    def test_get_metric_data(self, mock_parse_request, *args):
        metric_vo = MetricsFactory()
        mock_parse_request.return_value = ({}, {})

        metric_servicer = Metric()
        metric_data_info = metric_servicer.get_data({}, {})

        print_message(metric_data_info, 'test_get_metric_data')


if __name__ == "__main__":
    unittest.main(testRunner=RichTestRunner)
