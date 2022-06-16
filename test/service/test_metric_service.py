import unittest
import time
from datetime import datetime, timedelta
from unittest.mock import patch
from mongoengine import connect, disconnect

from spaceone.core.unittest.result import print_data
from spaceone.core.unittest.runner import RichTestRunner
from spaceone.core import config
from spaceone.core import utils
from spaceone.core.transaction import Transaction
from spaceone.monitoring.error import *
from spaceone.monitoring.model.data_source_model import DataSource
from spaceone.monitoring.service.metric_service import MetricService
from spaceone.monitoring.manager.plugin_manager import PluginManager
from spaceone.monitoring.manager.secret_manager import SecretManager
from spaceone.monitoring.manager.inventory_manager import InventoryManager
from spaceone.monitoring.manager.data_source_plugin_manager import DataSourcePluginManager
from spaceone.monitoring.connector.datasource_plugin_connector import DataSourcePluginConnector
from spaceone.monitoring.info.metric_info import *
from test.factory.data_source_factory import DataSourceFactory


class TestMetricService(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        config.init_conf(package='spaceone.monitoring')
        config.set_service_config()
        config.set_global(MOCK_MODE=True)
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

    def tearDown(self, *args) -> None:
        print()
        print('(tearDown) ==> Delete all data_sources')
        data_source_vos = DataSource.objects.filter()
        data_source_vos.delete()

    def _new_iter(self):
        return

    @patch.object(PluginManager, 'get_plugin_endpoint', return_value={'endpoint': 'grpc://plugin.spaceone.dev:50051', 'updated_version': '1.2'})
    @patch.object(DataSourcePluginManager, 'get_data_source_plugin_endpoint_by_vo', return_value='grpc://plugin.spaceone.dev:50051')
    @patch.object(DataSourcePluginConnector, 'initialize', return_value=None)
    @patch.object(SecretManager, 'get_secret_data', return_value={'data': {}})
    @patch.object(DataSourcePluginConnector, 'list_metrics')
    @patch.object(SecretManager, 'list_secrets')
    @patch.object(InventoryManager, 'list_resources')
    def test_list_metrics(self, mock_list_cloud_services, mock_list_secrets, mock_list_metrics, *args):
        cs_id_1 = utils.generate_id('cloud_service')
        cs_id_2 = utils.generate_id('cloud_service')
        cs_id_3 = utils.generate_id('cloud_service')

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

        mock_list_cloud_services.return_value = [
            {
                'cloud_service_id': cs_id_1,
                'region_code': 'ap-northeast-2',
                'reference': {'resource_id': 'arn:aws:ec2:ap-northeast-2:123456789012:instance/i-1234'},
                'collection_info': {'secrets': [utils.generate_id('secret')]}
            }, {
                'cloud_service_id': cs_id_2,
                'region_code': 'ap-northeast-2',
                'reference': {'resource_id': 'arn:aws:ec2:ap-northeast-2:123456789012:instance/i-4567'},
                'collection_info': {'secrets': [utils.generate_id('secret')]}
            }
        ]

        new_data_source_vo = DataSourceFactory(domain_id=self.domain_id)
        params = {
            'data_source_id': new_data_source_vo.data_source_id,
            'resource_type': 'inventory.CloudService',
            'resources': [cs_id_1, cs_id_2, cs_id_3],
            'domain_id': self.domain_id
        }

        self.transaction.method = 'list'
        metric_svc = MetricService(transaction=self.transaction)
        metrics_info = metric_svc.list(params.copy())

        print_data(metrics_info, 'test_list_metrics')
        MetricsInfo(metrics_info)

        self.assertEqual(params['domain_id'], metrics_info['domain_id'])

    @patch.object(PluginManager, 'get_plugin_endpoint', return_value={'endpoint': 'grpc://plugin.spaceone.dev:50051', 'updated_version': '1.2'})
    @patch.object(DataSourcePluginManager, 'get_data_source_plugin_endpoint_by_vo', return_value='grpc://plugin.spaceone.dev:50051')
    @patch.object(DataSourcePluginConnector, 'initialize', return_value=None)
    @patch.object(SecretManager, 'get_secret_data', return_value={'data': {}})
    @patch.object(DataSourcePluginConnector, 'get_metric_data')
    @patch.object(SecretManager, 'list_secrets')
    @patch.object(InventoryManager, 'list_resources')
    def test_get_metric_data(self, mock_list_cloud_services, mock_list_secrets, mock_get_metric_data, *args):
        cs_id_1 = utils.generate_id('cloud_service')
        cs_id_2 = utils.generate_id('cloud_service')
        cs_id_3 = utils.generate_id('cloud_service')
        cs_id_4 = utils.generate_id('cloud_service')
        cs_id_5 = utils.generate_id('cloud_service')
        cs_id_6 = utils.generate_id('cloud_service')
        cs_id_7 = utils.generate_id('cloud_service')

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

        mock_list_cloud_services.return_value = [
            {
                'cloud_service_id': cs_id_1,
                'data': {'cloudwatch': {}},
                'region_code': 'ap-northeast-2',
                'reference': {'resource_id': 'arn:aws:ec2:ap-northeast-2:123456789012:instance/i-1234'},
                'collection_info': {'secrets': [utils.generate_id('secret')]}
            }, {
                'cloud_service_id': cs_id_2,
                'data': {'cloudwatch': {}},
                'region_code': 'ap-northeast-2',
                'reference': {'resource_id': 'arn:aws:ec2:ap-northeast-2:123456789012:instance/i-4567'},
                'collection_info': {'secrets': [utils.generate_id('secret')]}
            }, {
                'cloud_service_id': cs_id_3,
                'data': {'cloudwatch': {}},
                'region_code': 'ap-northeast-2',
                'reference': {'resource_id': 'arn:aws:ec2:ap-northeast-2:123456789012:instance/i-4567'},
                'collection_info': {'secrets': [utils.generate_id('secret')]}
            }, {
                'cloud_service_id': cs_id_4,
                'data': {'cloudwatch': {}},
                'region_code': 'ap-northeast-2',
                'reference': {'resource_id': 'arn:aws:ec2:ap-northeast-2:123456789012:instance/i-4567'},
                'collection_info': {'secrets': [utils.generate_id('secret')]}
            }, {
                'cloud_service_id': cs_id_5,
                'data': {'cloudwatch': {}},
                'region_code': 'ap-northeast-2',
                'reference': {'resource_id': 'arn:aws:ec2:ap-northeast-2:123456789012:instance/i-4567'},
                'collection_info': {'secrets': [utils.generate_id('secret')]}
            }, {
                'cloud_service_id': cs_id_6,
                'data': {'cloudwatch': {}},
                'region_code': 'ap-northeast-2',
                'reference': {'resource_id': 'arn:aws:ec2:ap-northeast-2:123456789012:instance/i-4567'},
                'collection_info': {'secrets': [utils.generate_id('secret')]}
            }, {
                'cloud_service_id': cs_id_7,
                'data': {'cloudwatch': {}},
                'region_code': 'ap-northeast-2',
                'reference': {'resource_id': 'arn:aws:ec2:ap-northeast-2:123456789012:instance/i-4567'},
                'collection_info': {'secrets': [utils.generate_id('secret')]}
            }
        ]

        new_data_source_vo = DataSourceFactory(domain_id=self.domain_id)
        params = {
            'data_source_id': new_data_source_vo.data_source_id,
            'resource_type': 'inventory.CloudService',
            'resources': [cs_id_1, cs_id_2],
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
