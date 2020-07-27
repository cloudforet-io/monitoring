import unittest
from datetime import datetime, timedelta
from unittest.mock import patch
from mongoengine import connect, disconnect

from spaceone.core.unittest.result import print_data
from spaceone.core.unittest.runner import RichTestRunner
from spaceone.core import config
from spaceone.core import utils
from spaceone.core.model.mongo_model import MongoModel
from spaceone.core.transaction import Transaction
from spaceone.monitoring.error import *
from spaceone.monitoring.model.data_source_model import DataSource
from spaceone.monitoring.service.log_service import LogService
from spaceone.monitoring.connector.identity_connector import IdentityConnector
from spaceone.monitoring.connector.inventory_connector import InventoryConnector
from spaceone.monitoring.connector.monitoring_plugin_connector import MonitoringPluginConnector
from spaceone.monitoring.connector.plugin_connector import PluginConnector
from spaceone.monitoring.connector.secret_connector import SecretConnector
from spaceone.monitoring.info.log_info import *
from test.factory.data_source_factory import DataSourceFactory


class TestMetricService(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        config.init_conf(package='spaceone.monitoring')
        connect('test', host='mongomock://localhost')

        cls.domain_id = utils.generate_id('domain')
        cls.transaction = Transaction({
            'service': 'monitoring',
            'api_class': 'Log'
        })
        super().setUpClass()

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        disconnect()

    @patch.object(MongoModel, 'connect', return_value=None)
    def tearDown(self, *args) -> None:
        print()
        print('(tearDown) ==> Delete all data_sources')
        data_source_vos = DataSource.objects.filter()
        data_source_vos.delete()

    def _new_iter(self):
        return

    @patch.object(MongoModel, 'connect', return_value=None)
    @patch.object(IdentityConnector, '__init__', return_value=None)
    @patch.object(InventoryConnector, '__init__', return_value=None)
    @patch.object(SecretConnector, '__init__', return_value=None)
    @patch.object(PluginConnector, '__init__', return_value=None)
    @patch.object(PluginConnector, 'get_plugin_endpoint', return_value='grpc://plugin.spaceone.dev:50051')
    @patch.object(SecretConnector, 'get_secret_data', return_value={'data': {}})
    @patch.object(InventoryConnector, 'get_server')
    @patch.object(SecretConnector, 'list_secrets')
    @patch.object(MonitoringPluginConnector, 'list_logs')
    def test_list_server_logs(self, mock_list_logs, mock_list_secrets, mock_get_server, *args):
        server_id = utils.generate_id('server')
        end = datetime.utcnow()
        start = end - timedelta(days=1)

        mock_list_logs.return_value.__iter__ = lambda response: iter([{
            'resource_type': 'monitoring.Log',
            'result': {
                'logs': [{
                    'key1': 'value1',
                    'key2': 'value2',
                    'key3': 'value3'
                }]
            }
        }])

        mock_list_secrets.return_value = {
            'results': [{
                'secret_id': utils.generate_id('secret')
            }],
            'total_count': 1
        }

        mock_get_server.return_value = {
            'server_id': server_id,
            'reference': {'resource_id': 'arn:aws:ec2:ap-northeast-2:123456789012:instance/i-1234'},
            'collection_info': {'secrets': [utils.generate_id('secret')]}
        }

        new_data_source_vo = DataSourceFactory(domain_id=self.domain_id)
        params = {
            'data_source_id': new_data_source_vo.data_source_id,
            'resource_type': 'inventory.Server',
            'resource_id': server_id,
            'start': start.isoformat(),
            'end': end.isoformat(),
            'sort': {
                'key': 'EventId',
                'desc': False
            },
            'limit': 10,
            'domain_id': self.domain_id
        }

        self.transaction.method = 'list'
        log_svc = LogService(transaction=self.transaction)
        logs_data_info = log_svc.list(params.copy())

        print_data(logs_data_info, 'test_list_logs')
        LogDataInfo(logs_data_info)

        self.assertEqual(params['domain_id'], logs_data_info['domain_id'])

    @patch.object(MongoModel, 'connect', return_value=None)
    @patch.object(IdentityConnector, '__init__', return_value=None)
    @patch.object(InventoryConnector, '__init__', return_value=None)
    @patch.object(SecretConnector, '__init__', return_value=None)
    @patch.object(PluginConnector, '__init__', return_value=None)
    @patch.object(PluginConnector, 'get_plugin_endpoint', return_value='grpc://plugin.spaceone.dev:50051')
    @patch.object(SecretConnector, 'get_secret_data', return_value={'data': {}})
    @patch.object(IdentityConnector, 'get_service_account')
    @patch.object(SecretConnector, 'list_secrets')
    @patch.object(MonitoringPluginConnector, 'list_logs')
    def test_list_service_account_logs(self, mock_list_logs, mock_list_secrets, mock_get_server, *args):
        service_account_id = utils.generate_id('sa')
        end = datetime.utcnow()
        start = end - timedelta(days=1)

        mock_list_logs.return_value.__iter__ = lambda response: iter([{
            'resource_type': 'monitoring.Log',
            'result': {
                'logs': [{
                    'key1': 'value1',
                    'key2': 'value2',
                    'key3': 'value3'
                }]
            }
        }])

        mock_list_secrets.return_value = {
            'results': [{
                'secret_id': utils.generate_id('secret')
            }],
            'total_count': 1
        }

        mock_get_server.return_value = {
            'service_account_id': service_account_id
        }

        new_data_source_vo = DataSourceFactory(domain_id=self.domain_id)
        params = {
            'data_source_id': new_data_source_vo.data_source_id,
            'resource_type': 'identity.ServiceAccount',
            'resource_id': service_account_id,
            'filter': {},
            'start': start.isoformat(),
            'end': end.isoformat(),
            'sort': {
                'key': 'EventId',
                'desc': False
            },
            'limit': 10,
            'domain_id': self.domain_id
        }

        self.transaction.method = 'list'
        log_svc = LogService(transaction=self.transaction)
        logs_data_info = log_svc.list(params.copy())

        print_data(logs_data_info, 'test_list_logs')
        LogDataInfo(logs_data_info)

        self.assertEqual(params['domain_id'], logs_data_info['domain_id'])


if __name__ == "__main__":
    unittest.main(testRunner=RichTestRunner)
