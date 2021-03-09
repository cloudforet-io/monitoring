import unittest
import time
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
from spaceone.monitoring.service.metric_service import MetricService
from spaceone.monitoring.connector.inventory_connector import InventoryConnector
from spaceone.monitoring.connector.monitoring_plugin_connector import MonitoringPluginConnector
from spaceone.monitoring.connector.plugin_connector import PluginConnector
from spaceone.monitoring.connector.secret_connector import SecretConnector
from spaceone.monitoring.info.metric_info import *
from test.factory.data_source_factory import DataSourceFactory


class TestMetricService(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        config.init_conf(package='spaceone.monitoring')
        connect('test', host='mongomock://localhost')

        cls.domain_id = utils.generate_id('domain')
        cls.transaction = Transaction({
            'service': 'monitoring',
            'api_class': 'Metric'
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
    @patch.object(InventoryConnector, '__init__', return_value=None)
    @patch.object(SecretConnector, '__init__', return_value=None)
    @patch.object(PluginConnector, '__init__', return_value=None)
    @patch.object(PluginConnector, 'get_plugin_endpoint', return_value='grpc://plugin.spaceone.dev:50051')
    @patch.object(SecretConnector, 'get_secret_data', return_value={'data': {}})
    @patch.object(InventoryConnector, 'list_servers')
    @patch.object(SecretConnector, 'list_secrets')
    @patch.object(MonitoringPluginConnector, 'list_metrics')
    def test_list_metrics(self, mock_list_metrics, mock_list_secrets, mock_list_servers, *args):
        server_id_1 = utils.generate_id('server')
        server_id_2 = utils.generate_id('server')
        server_id_3 = utils.generate_id('server')

        mock_list_metrics.return_value = {
            'resource_type': 'monitoring.Metric',
            'result': {
                'metrics': [{
                    'key': 'cpu',
                    'name': 'CPU Utilization',
                    'unit': {
                        'x': 'Datetime',
                        'y': '%'
                    },
                    'chart_type': 'line'
                }, {
                    'key': 'memory',
                    'name': 'Memory Usage',
                    'unit': {
                        'x': 'Datetime',
                        'y': '%'
                    },
                    'chart_type': 'line'
                }]
            }
        }

        mock_list_secrets.return_value = {
            'results': [{
                'secret_id': utils.generate_id('secret'),
                'schema': 'aws_access_key'
            }],
            'total_count': 1
        }

        mock_list_servers.return_value = {
            'results': [{
                'server_id': server_id_1,
                'reference': {'resource_id': 'arn:aws:ec2:ap-northeast-2:123456789012:instance/i-1234'},
                'collection_info': {'secrets': [utils.generate_id('secret')]}
            }, {
                'server_id': server_id_2,
                'reference': {'resource_id': 'arn:aws:ec2:ap-northeast-2:123456789012:instance/i-4567'},
                'collection_info': {'secrets': [utils.generate_id('secret')]}
            }],
            'total_count': 2
        }

        new_data_source_vo = DataSourceFactory(domain_id=self.domain_id)
        params = {
            'data_source_id': new_data_source_vo.data_source_id,
            'resource_type': 'inventory.Server',
            'resources': [server_id_1, server_id_2, server_id_3],
            'domain_id': self.domain_id
        }

        self.transaction.method = 'list'
        metric_svc = MetricService(transaction=self.transaction)
        metrics_info = metric_svc.list(params.copy())

        print_data(metrics_info, 'test_list_metrics')
        MetricsInfo(metrics_info)

        self.assertEqual(params['domain_id'], metrics_info['domain_id'])

    @patch.object(MongoModel, 'connect', return_value=None)
    @patch.object(InventoryConnector, '__init__', return_value=None)
    @patch.object(SecretConnector, '__init__', return_value=None)
    @patch.object(PluginConnector, '__init__', return_value=None)
    @patch.object(PluginConnector, 'get_plugin_endpoint', return_value='grpc://plugin.spaceone.dev:50051')
    @patch.object(SecretConnector, 'get_secret_data', return_value={'data': {}})
    @patch.object(InventoryConnector, 'list_servers')
    @patch.object(SecretConnector, 'list_secrets')
    @patch.object(MonitoringPluginConnector, 'get_metric_data')
    def test_get_metric_data(self, mock_get_metric_data, mock_list_secrets, mock_list_servers, *args):
        server_id_1 = utils.generate_id('server')
        server_id_2 = utils.generate_id('server')
        end = datetime.utcnow()
        start = end - timedelta(days=1)
        start_ts = int(time.mktime(start.timetuple()))

        mock_get_metric_data.return_value = {
            'labels': [start_ts, start_ts + 3600, start_ts + (3600 * 2), start_ts + (3600 * 3),
                       start_ts + (3600 * 4)],
            'values': [1, 2, 3, 4, 5]
        }

        mock_list_secrets.return_value = {
            'results': [{
                'secret_id': utils.generate_id('secret')
            }],
            'total_count': 1
        }

        mock_list_servers.return_value = {
            'results': [{
                'server_id': server_id_1,
                'reference': {'resource_id': 'arn:aws:ec2:ap-northeast-2:123456789012:instance/i-1234'},
                'collection_info': {'secrets': [utils.generate_id('secret')]}
            }, {
                'server_id': server_id_2,
                'reference': {'resource_id': 'arn:aws:ec2:ap-northeast-2:123456789012:instance/i-4567'},
                'collection_info': {'secrets': [utils.generate_id('secret')]}
            }],
            'total_count': 2
        }

        new_data_source_vo = DataSourceFactory(domain_id=self.domain_id)
        params = {
            'data_source_id': new_data_source_vo.data_source_id,
            'resource_type': 'inventory.Server',
            'resources': [server_id_1, server_id_2],
            'metric': 'cpu',
            'start': start.isoformat(),
            'end': end.isoformat(),
            'domain_id': self.domain_id
        }

        self.transaction.method = 'get_data'
        metric_svc = MetricService(transaction=self.transaction)
        metrics_data_info = metric_svc.get_data(params.copy())

        print_data(metrics_data_info, 'test_get_metric_data')
        MetricDataInfo(metrics_data_info)

        self.assertEqual(params['domain_id'], metrics_data_info['domain_id'])


if __name__ == "__main__":
    unittest.main(testRunner=RichTestRunner)
