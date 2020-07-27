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
from spaceone.api.monitoring.v1 import log_pb2
from spaceone.monitoring.api.v1.log import Log
from test.factory.log_factory import LogDataFactory


class _MockLogService(BaseService):

    def list(self, params):
        return LogDataFactory()


class TestLogAPI(unittest.TestCase):

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
    @patch.object(Locator, 'get_service', return_value=_MockLogService())
    @patch.object(BaseAPI, 'parse_request')
    def test_list_logs(self, mock_parse_request, *args):
        print(LogDataFactory())
        mock_parse_request.return_value = ({}, {})

        log_servicer = Log()
        logs_info = log_servicer.list({}, {})

        print_message(logs_info, 'test_list_logs')


if __name__ == "__main__":
    unittest.main(testRunner=RichTestRunner)
