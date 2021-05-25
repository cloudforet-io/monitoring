import unittest
import copy
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
from spaceone.api.monitoring.v1 import data_source_pb2
from spaceone.monitoring.interface.grpc.v1.data_source import DataSource
from test.factory.data_source_factory import DataSourceFactory


class _MockDataSourceService(BaseService):

    def register(self, params):
        params = copy.deepcopy(params)
        if 'tags' in params:
            params['tags'] = utils.dict_to_tags(params['tags'])

        return DataSourceFactory(**params)

    def update(self, params):
        params = copy.deepcopy(params)
        if 'tags' in params:
            params['tags'] = utils.dict_to_tags(params['tags'])

        return DataSourceFactory(**params)

    def deregister(self, params):
        pass

    def enable(self, params):
        return DataSourceFactory(**params)

    def disable(self, params):
        return DataSourceFactory(**params)

    def update_plugin(self, params):
        params['plugin_info'] = {}
        params['plugin_info']['version'] = params.get('version')
        params['plugin_info']['options'] = params.get('options')
        del params['version']
        del params['options']
        return DataSourceFactory(**params)

    def verify_plugin(self, params):
        pass

    def get(self, params):
        return DataSourceFactory(**params)

    def list(self, params):
        return DataSourceFactory.build_batch(10, **params), 10


class TestDataSourceAPI(unittest.TestCase):

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
    @patch.object(Locator, 'get_service', return_value=_MockDataSourceService())
    @patch.object(BaseAPI, 'parse_request')
    def test_register_data_source(self, mock_parse_request, *args):
        params = {
            'name': utils.random_string(),
            'monitoring_type': 'METRIC',
            'tags': {
                utils.random_string(): utils.random_string()
            },
            'plugin_info': {
                'plugin_id': utils.generate_id('plugin'),
                'version': '1.1',
                'secret_id': utils.generate_id('secret')
            },
            'domain_id': utils.generate_id('domain')
        }
        mock_parse_request.return_value = (params, {})

        data_source_servicer = DataSource()
        data_source_info = data_source_servicer.register({}, {})

        print_message(data_source_info, 'test_register_data_source')

        data_source_data = MessageToDict(data_source_info, preserving_proto_field_name=True)
        self.assertIsInstance(data_source_info, data_source_pb2.DataSourceInfo)
        self.assertEqual(data_source_info.name, params['name'])
        self.assertEqual(data_source_info.state, data_source_pb2.DataSourceInfo.State.ENABLED)
        self.assertEqual(data_source_info.monitoring_type, data_source_pb2.MonitoringType.METRIC)
        self.assertIsNotNone(data_source_info.provider)
        self.assertIsNotNone(data_source_info.capability)
        self.assertDictEqual(data_source_data['tags'], params['tags'])
        self.assertIsInstance(data_source_info.plugin_info, data_source_pb2.DataSourcePluginInfo)
        self.assertEqual(data_source_data['plugin_info']['plugin_id'], params['plugin_info']['plugin_id'])
        self.assertEqual(data_source_data['plugin_info']['version'], params['plugin_info']['version'])
        self.assertEqual(data_source_data['plugin_info']['secret_id'], params['plugin_info']['secret_id'])
        self.assertEqual(data_source_info.domain_id, params['domain_id'])
        self.assertIsNotNone(getattr(data_source_info, 'created_at', None))

    @patch.object(BaseAPI, '__init__', return_value=None)
    @patch.object(Locator, 'get_service', return_value=_MockDataSourceService())
    @patch.object(BaseAPI, 'parse_request')
    def test_update_data_source(self, mock_parse_request, *args):
        params = {
            'name': utils.random_string(),
            'tags': {
                'update_key': 'update_value'
            },
            'domain_id': utils.generate_id('domain')
        }
        mock_parse_request.return_value = (params, {})

        data_source_servicer = DataSource()
        data_source_info = data_source_servicer.update({}, {})

        print_message(data_source_info, 'test_update_data_source')
        data_source_data = MessageToDict(data_source_info, preserving_proto_field_name=True)
        self.assertIsInstance(data_source_info, data_source_pb2.DataSourceInfo)
        self.assertEqual(data_source_info.name, params['name'])
        self.assertDictEqual(data_source_data['tags'], params['tags'])

    @patch.object(BaseAPI, '__init__', return_value=None)
    @patch.object(Locator, 'get_service', return_value=_MockDataSourceService())
    @patch.object(BaseAPI, 'parse_request')
    def test_deregister_data_source(self, mock_parse_request, *args):
        mock_parse_request.return_value = ({}, {})

        data_source_servicer = DataSource()
        data_source_info = data_source_servicer.deregister({}, {})

        print_message(data_source_info, 'test_deregister_data_source')

        self.assertIsInstance(data_source_info, Empty)

    @patch.object(BaseAPI, '__init__', return_value=None)
    @patch.object(Locator, 'get_service', return_value=_MockDataSourceService())
    @patch.object(BaseAPI, 'parse_request')
    def test_enable_data_source(self, mock_parse_request, *args):
        params = {
            'data_source_id': utils.generate_id('data_source'),
            'state': 'ENABLED',
            'domain_id': utils.generate_id('domain')
        }
        mock_parse_request.return_value = (params, {})

        data_source_servicer = DataSource()
        data_source_info = data_source_servicer.enable({}, {})

        print_message(data_source_info, 'test_enable_data_source')

        self.assertIsInstance(data_source_info, data_source_pb2.DataSourceInfo)
        self.assertEqual(data_source_info.state, data_source_pb2.DataSourceInfo.State.ENABLED)

    @patch.object(BaseAPI, '__init__', return_value=None)
    @patch.object(Locator, 'get_service', return_value=_MockDataSourceService())
    @patch.object(BaseAPI, 'parse_request')
    def test_disable_data_source(self, mock_parse_request, *args):
        params = {
            'data_source_id': utils.generate_id('data_source'),
            'state': 'DISABLED',
            'domain_id': utils.generate_id('domain')
        }
        mock_parse_request.return_value = (params, {})

        data_source_servicer = DataSource()
        data_source_info = data_source_servicer.disable({}, {})

        print_message(data_source_info, 'test_disable_data_source')

        self.assertIsInstance(data_source_info, data_source_pb2.DataSourceInfo)
        self.assertEqual(data_source_info.state, data_source_pb2.DataSourceInfo.State.DISABLED)

    @patch.object(BaseAPI, '__init__', return_value=None)
    @patch.object(Locator, 'get_service', return_value=_MockDataSourceService())
    @patch.object(BaseAPI, 'parse_request')
    def test_update_plugin(self, mock_parse_request, *args):
        params = {
            'data_source_id': utils.generate_id('data_source'),
            'domain_id': utils.generate_id('domain'),
            'version': "1.1",
            'options': {}
        }
        mock_parse_request.return_value = (params, {})

        data_source_servicer = DataSource()
        data_source_info = data_source_servicer.update_plugin({}, {})
        print_message(data_source_info, 'test_update_data_source')
        data_source_data = MessageToDict(data_source_info, preserving_proto_field_name=True)
        self.assertIsInstance(data_source_info, data_source_pb2.DataSourceInfo)
        self.assertEqual(data_source_info.plugin_info.version, "1.1")


    @patch.object(BaseAPI, '__init__', return_value=None)
    @patch.object(Locator, 'get_service', return_value=_MockDataSourceService())
    @patch.object(BaseAPI, 'parse_request')
    def test_verify_plugin(self, mock_parse_request, *args):
        params = {
            'data_source_id': utils.generate_id('data_source'),
            'secret_id': utils.generate_id('secret'),
            'domain_id': utils.generate_id('domain')
        }
        mock_parse_request.return_value = (params, {})

        data_source_servicer = DataSource()
        verify_info = data_source_servicer.verify_plugin({}, {})

        print_message(verify_info, 'test_verify_plugin')

        self.assertIsInstance(verify_info, data_source_pb2.VerifyInfo)

    @patch.object(BaseAPI, '__init__', return_value=None)
    @patch.object(Locator, 'get_service', return_value=_MockDataSourceService())
    @patch.object(BaseAPI, 'parse_request')
    def test_get_data_source(self, mock_parse_request, *args):
        mock_parse_request.return_value = ({}, {})

        data_source_servicer = DataSource()
        data_source_info = data_source_servicer.get({}, {})

        print_message(data_source_info, 'test_get_data_source')

        self.assertIsInstance(data_source_info, data_source_pb2.DataSourceInfo)

    @patch.object(BaseAPI, '__init__', return_value=None)
    @patch.object(Locator, 'get_service', return_value=_MockDataSourceService())
    @patch.object(BaseAPI, 'parse_request')
    def test_list_data_sources(self, mock_parse_request, *args):
        mock_parse_request.return_value = ({}, {})

        data_source_servicer = DataSource()
        data_sources_info = data_source_servicer.list({}, {})

        print_message(data_sources_info, 'test_list_data_source')

        self.assertIsInstance(data_sources_info, data_source_pb2.DataSourcesInfo)
        self.assertIsInstance(data_sources_info.results[0], data_source_pb2.DataSourceInfo)
        self.assertEqual(data_sources_info.total_count, 10)


if __name__ == "__main__":
    unittest.main(testRunner=RichTestRunner)
