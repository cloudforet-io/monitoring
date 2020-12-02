import unittest
from unittest.mock import patch
from mongoengine import connect, disconnect

from spaceone.core.unittest.result import print_data
from spaceone.core.unittest.runner import RichTestRunner
from spaceone.core import config
from spaceone.core import utils
from spaceone.core.model.mongo_model import MongoModel
from spaceone.core.transaction import Transaction
from spaceone.monitoring.error import *
from spaceone.monitoring.service.data_source_service import DataSourceService
from spaceone.monitoring.model.data_source_model import DataSource
from spaceone.monitoring.connector.monitoring_plugin_connector import MonitoringPluginConnector
from spaceone.monitoring.connector.plugin_connector import PluginConnector
from spaceone.monitoring.connector.repository_connector import RepositoryConnector
from spaceone.monitoring.connector.secret_connector import SecretConnector
from spaceone.monitoring.info.data_source_info import *
from spaceone.monitoring.info.common_info import StatisticsInfo
from test.factory.data_source_factory import DataSourceFactory


class TestDataSourceService(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        config.init_conf(package='spaceone.monitoring')
        connect('test', host='mongomock://localhost')

        cls.domain_id = utils.generate_id('domain')
        cls.transaction = Transaction({
            'service': 'monitoring',
            'api_class': 'DataSource'
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

    @patch.object(MongoModel, 'connect', return_value=None)
    @patch.object(RepositoryConnector, '__init__', return_value=None)
    @patch.object(SecretConnector, '__init__', return_value=None)
    @patch.object(PluginConnector, '__init__', return_value=None)
    @patch.object(PluginConnector, 'get_plugin_endpoint', return_value='grpc://plugin.spaceone.dev:50051')
    @patch.object(SecretConnector, 'get_secret_data', return_value={'data': {}})
    @patch.object(RepositoryConnector, 'get_plugin_versions', return_value=['1.0', '1.1', '1.2'])
    @patch.object(RepositoryConnector, 'get_plugin')
    @patch.object(SecretConnector, 'list_secrets')
    @patch.object(MonitoringPluginConnector, 'verify')
    def test_register_metric_data_source_with_secret_id(self, mock_plugin_verify, mock_list_secrets,
                                                        mock_get_plugin, *args):
        secret_id = utils.generate_id('secret')
        plugin_id = utils.generate_id('plugin')
        plugin_version = '1.0'

        mock_plugin_verify.return_value.__iter__ = lambda response: iter([{
            'resource_type': 'monitoring.DataSource',
            'result': {
                'options': {
                    'supported_resource_type': ['inventory.Server', 'inventory.CloudService'],
                    'supported_stat': ['AVERAGE', 'MAX', 'MIN'],
                    'reference_keys': [{
                        'resource_type': 'inventory.Server',
                        'reference_key': 'reference.resource_id'
                    }]
                }
            }
        }])

        mock_list_secrets.return_value = {
            'results': [{
                'secret_id': secret_id,
                'schema': 'aws_access_key'
            }],
            'total_count': 1
        }

        mock_get_plugin.return_value = {
            'capability': {
                'supported_schema': ['aws_access_key', 'aws_assume_role'],
                'monitoring_type': 'METRIC'
            },
            'provider': 'aws'
        }

        params = {
            'name': 'AWS CloudWatch',
            'plugin_info': {
                'plugin_id': plugin_id,
                'version': plugin_version,
                'options': {},
                'secret_id': secret_id
            },
            'tags': [
                {
                    'key': 'tag_key',
                    'value': 'tag_value'
                }
            ],
            'domain_id': self.domain_id
        }

        self.transaction.method = 'register'
        data_source_svc = DataSourceService(transaction=self.transaction)
        data_source_vo = data_source_svc.register(params.copy())

        print_data(data_source_vo.to_dict(), 'test_register_metric_data_source_with_secret_id')
        DataSourceInfo(data_source_vo)

        self.assertIsInstance(data_source_vo, DataSource)
        self.assertEqual(params['name'], data_source_vo.name)
        self.assertEqual(params.get('tags', {}), data_source_vo.to_dict()['tags'])
        self.assertEqual(params['domain_id'], data_source_vo.domain_id)

    @patch.object(MongoModel, 'connect', return_value=None)
    @patch.object(RepositoryConnector, '__init__', return_value=None)
    @patch.object(SecretConnector, '__init__', return_value=None)
    @patch.object(PluginConnector, '__init__', return_value=None)
    @patch.object(PluginConnector, 'get_plugin_endpoint', return_value='grpc://plugin.spaceone.dev:50051')
    @patch.object(SecretConnector, 'get_secret_data', return_value={'data': {}})
    @patch.object(RepositoryConnector, 'get_plugin_versions', return_value=['1.0', '1.1', '1.2'])
    @patch.object(RepositoryConnector, 'get_plugin')
    @patch.object(SecretConnector, 'list_secrets')
    @patch.object(MonitoringPluginConnector, 'verify')
    def test_register_metric_data_source_with_provider(self, mock_plugin_verify, mock_list_secrets,
                                                       mock_get_plugin, *args):
        plugin_id = utils.generate_id('plugin')
        plugin_version = '1.0'

        mock_plugin_verify.return_value.__iter__ = lambda response: iter([{
            'resource_type': 'monitoring.DataSource',
            'result': {
                'options': {
                    'supported_resource_type': ['inventory.Server', 'inventory.CloudService'],
                    'supported_stat': ['AVERAGE', 'MAX', 'MIN'],
                    'reference_keys': [{
                        'resource_type': 'inventory.Server',
                        'reference_key': 'reference.resource_id'
                    }]
                }
            }
        }])

        mock_list_secrets.return_value = {
            'results': [{
                'secret_id': utils.generate_id('secret'),
                'schema': 'aws_access_key'
            }],
            'total_count': 1
        }

        mock_get_plugin.return_value = {
            'capability': {
                'use_resource_secret': True,
                'supported_schema': ['aws_access_key', 'aws_assume_role'],
                'monitoring_type': 'METRIC'
            },
            'provider': 'aws'
        }

        params = {
            'name': 'AWS CloudWatch',
            'plugin_info': {
                'plugin_id': plugin_id,
                'version': plugin_version,
                'options': {},
                'provider': 'aws'
            },
            'tags': [
                {
                    'key': 'tag_key',
                    'value': 'tag_value'
                }
            ],
            'domain_id': self.domain_id
        }

        self.transaction.method = 'register'
        data_source_svc = DataSourceService(transaction=self.transaction)
        data_source_vo = data_source_svc.register(params.copy())

        print_data(data_source_vo.to_dict(), 'test_register_metric_data_source_with_provider')
        DataSourceInfo(data_source_vo)

        self.assertIsInstance(data_source_vo, DataSource)
        self.assertEqual(params['name'], data_source_vo.name)
        self.assertEqual(params.get('tags', {}), data_source_vo.to_dict()['tags'])
        self.assertEqual(params['domain_id'], data_source_vo.domain_id)

    @patch.object(MongoModel, 'connect', return_value=None)
    @patch.object(SecretConnector, '__init__', return_value=None)
    @patch.object(PluginConnector, '__init__', return_value=None)
    @patch.object(PluginConnector, 'get_plugin_endpoint', return_value='grpc://plugin.spaceone.dev:50051')
    @patch.object(SecretConnector, 'get_secret_data', return_value={'data': {}})
    @patch.object(SecretConnector, 'list_secrets')
    @patch.object(MonitoringPluginConnector, 'init')
    def test_update_data_source(self, mock_plugin_init, mock_list_secrets, *args):
        mock_plugin_init.return_value = {
            'metadata': {
                'supported_resource_type': ['inventory.Server'],
                'supported_stat': ['AVERAGE', 'MAX', 'MIN'],
                'reference_keys': [{
                    'resource_type': 'inventory.Server',
                    'reference_key': 'reference.resource_id'
                }]
            }
        }

        mock_list_secrets.return_value = {
            'results': [{
                'secret_id': utils.generate_id('secret')
            }],
            'total_count': 1
        }

        new_data_source_vo = DataSourceFactory(domain_id=self.domain_id)
        params = {
            'data_source_id': new_data_source_vo.data_source_id,
            'name': 'Update AWS CloudWatch',
            'plugin_info': {
                'plugin_id': new_data_source_vo.plugin_info.plugin_id,
                'version': '2.0',
                'options': {},
                'provider': 'aws'
            },
            'tags': [
                {
                    'key': 'update_key',
                    'value': 'update_value'
                }
            ],
            'domain_id': self.domain_id
        }

        self.transaction.method = 'update'
        data_source_svc = DataSourceService(transaction=self.transaction)
        data_source_vo = data_source_svc.update(params.copy())

        print_data(data_source_vo.to_dict(), 'test_update_data_source')
        DataSourceInfo(data_source_vo)

        self.assertIsInstance(data_source_vo, DataSource)
        self.assertEqual(new_data_source_vo.data_source_id, data_source_vo.data_source_id)
        self.assertEqual(params['name'], data_source_vo.name)
        self.assertEqual(params.get('tags', {}), data_source_vo.to_dict()['tags'])

    @patch.object(MongoModel, 'connect', return_value=None)
    def test_enable_data_source(self, *args):
        new_data_source_vo = DataSourceFactory(domain_id=self.domain_id, state='DISABLED')
        params = {
            'data_source_id': new_data_source_vo.data_source_id,
            'domain_id': self.domain_id
        }

        self.transaction.method = 'enable'
        data_source_svc = DataSourceService(transaction=self.transaction)
        data_source_vo = data_source_svc.enable(params.copy())

        print_data(data_source_vo.to_dict(), 'test_enable_data_source')
        DataSourceInfo(data_source_vo)

        self.assertIsInstance(data_source_vo, DataSource)
        self.assertEqual(new_data_source_vo.data_source_id, data_source_vo.data_source_id)
        self.assertEqual('ENABLED', data_source_vo.state)

    @patch.object(MongoModel, 'connect', return_value=None)
    def test_disable_data_source(self, *args):
        new_data_source_vo = DataSourceFactory(domain_id=self.domain_id, state='ENABLED')
        params = {
            'data_source_id': new_data_source_vo.data_source_id,
            'domain_id': self.domain_id
        }

        self.transaction.method = 'disable'
        data_source_svc = DataSourceService(transaction=self.transaction)
        data_source_vo = data_source_svc.disable(params.copy())

        print_data(data_source_vo.to_dict(), 'test_disable_data_source')
        DataSourceInfo(data_source_vo)

        self.assertIsInstance(data_source_vo, DataSource)
        self.assertEqual(new_data_source_vo.data_source_id, data_source_vo.data_source_id)
        self.assertEqual('DISABLED', data_source_vo.state)

    @patch.object(MongoModel, 'connect', return_value=None)
    def test_deregister_data_source(self, *args):
        new_data_source_vo = DataSourceFactory(domain_id=self.domain_id)
        params = {
            'data_source_id': new_data_source_vo.data_source_id,
            'domain_id': self.domain_id
        }

        self.transaction.method = 'deregister'
        data_source_svc = DataSourceService(transaction=self.transaction)
        result = data_source_svc.deregister(params)

        self.assertIsNone(result)

    @patch.object(MongoModel, 'connect', return_value=None)
    def test_get_data_source(self, *args):
        new_data_source_vo = DataSourceFactory(domain_id=self.domain_id)
        params = {
            'data_source_id': new_data_source_vo.data_source_id,
            'domain_id': self.domain_id
        }

        self.transaction.method = 'get'
        data_source_svc = DataSourceService(transaction=self.transaction)
        data_source_vo = data_source_svc.get(params)

        print_data(data_source_vo.to_dict(), 'test_get_data_source')
        DataSourceInfo(data_source_vo)

        self.assertIsInstance(data_source_vo, DataSource)

    @patch.object(MongoModel, 'connect', return_value=None)
    def test_list_data_sources_by_data_source_id(self, *args):
        data_source_vos = DataSourceFactory.build_batch(10, domain_id=self.domain_id)
        list(map(lambda vo: vo.save(), data_source_vos))

        params = {
            'data_source_id': data_source_vos[0].data_source_id,
            'domain_id': self.domain_id
        }

        self.transaction.method = 'list'
        data_source_svc = DataSourceService(transaction=self.transaction)
        data_sources_vos, total_count = data_source_svc.list(params)
        DataSourcesInfo(data_source_vos, total_count)

        self.assertEqual(len(data_sources_vos), 1)
        self.assertIsInstance(data_sources_vos[0], DataSource)
        self.assertEqual(total_count, 1)

    @patch.object(MongoModel, 'connect', return_value=None)
    def test_list_data_sources_by_name(self, *args):
        data_source_vos = DataSourceFactory.build_batch(10, domain_id=self.domain_id)
        list(map(lambda vo: vo.save(), data_source_vos))

        params = {
            'name': data_source_vos[0].name,
            'domain_id': self.domain_id
        }

        self.transaction.method = 'list'
        data_source_svc = DataSourceService(transaction=self.transaction)
        data_sources_vos, total_count = data_source_svc.list(params)
        DataSourcesInfo(data_source_vos, total_count)

        self.assertEqual(len(data_sources_vos), 1)
        self.assertIsInstance(data_sources_vos[0], DataSource)
        self.assertEqual(total_count, 1)

    @patch.object(MongoModel, 'connect', return_value=None)
    def test_list_data_sources_by_monitoring_type(self, *args):
        data_source_vos = DataSourceFactory.build_batch(10, monitoring_type='METRIC', domain_id=self.domain_id)
        list(map(lambda vo: vo.save(), data_source_vos))

        params = {
            'monitoring_type': 'METRIC',
            'domain_id': self.domain_id
        }

        self.transaction.method = 'list'
        data_source_svc = DataSourceService(transaction=self.transaction)
        data_sources_vos, total_count = data_source_svc.list(params)
        DataSourcesInfo(data_source_vos, total_count)

        self.assertEqual(len(data_sources_vos), 10)
        self.assertIsInstance(data_sources_vos[0], DataSource)
        self.assertEqual(total_count, 10)

    @patch.object(MongoModel, 'connect', return_value=None)
    def test_list_data_sources_by_tag(self, *args):
        DataSourceFactory(tags=[{'key': 'tag_key_1', 'value': 'tag_value_1'}], domain_id=self.domain_id)
        data_source_vos = DataSourceFactory.build_batch(9, domain_id=self.domain_id)
        list(map(lambda vo: vo.save(), data_source_vos))

        params = {
            'query': {
                'filter': [{
                    'k': 'tags.tag_key_1',
                    'v': 'tag_value_1',
                    'o': 'eq'
                }]
            },
            'domain_id': self.domain_id
        }

        self.transaction.method = 'list'
        data_source_svc = DataSourceService(transaction=self.transaction)
        data_sources_vos, total_count = data_source_svc.list(params)
        DataSourcesInfo(data_source_vos, total_count)

        self.assertEqual(len(data_sources_vos), 1)
        self.assertIsInstance(data_sources_vos[0], DataSource)
        self.assertEqual(total_count, 1)

    @patch.object(MongoModel, 'connect', return_value=None)
    def test_stat_data_source(self, *args):
        data_source_vos = DataSourceFactory.build_batch(10, domain_id=self.domain_id)
        list(map(lambda vo: vo.save(), data_source_vos))

        params = {
            'domain_id': self.domain_id,
            'query': {
                'aggregate': {
                    'group': {
                        'keys': [{
                            'key': 'data_source_id',
                            'name': 'Id'
                        }],
                        'fields': [{
                            'operator': 'count',
                            'name': 'Count'
                        }]
                    }
                },
                'sort': {
                    'name': 'Count',
                    'desc': True
                }
            }
        }

        self.transaction.method = 'stat'
        data_source_svc = DataSourceService(transaction=self.transaction)
        values = data_source_svc.stat(params)
        StatisticsInfo(values)

        print_data(values, 'test_stat_data_source')

    @patch.object(MongoModel, 'connect', return_value=None)
    def test_stat_data_source_distinct(self, *args):
        data_source_vos = DataSourceFactory.build_batch(10, domain_id=self.domain_id)
        list(map(lambda vo: vo.save(), data_source_vos))

        params = {
            'domain_id': self.domain_id,
            'query': {
                'distinct': 'data_source_id',
                'page': {
                    'start': 2,
                    'limit': 3
                }
            }
        }

        self.transaction.method = 'stat'
        data_source_svc = DataSourceService(transaction=self.transaction)
        values = data_source_svc.stat(params)
        StatisticsInfo(values)

        print_data(values, 'test_stat_data_source_distinct')


if __name__ == "__main__":
    unittest.main(testRunner=RichTestRunner)
