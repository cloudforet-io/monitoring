import logging
import traceback
import concurrent.futures
from spaceone.core.service import *

from spaceone.monitoring.error import *
from spaceone.monitoring.manager.inventory_manager import InventoryManager
from spaceone.monitoring.manager.secret_manager import SecretManager
from spaceone.monitoring.manager.data_source_manager import DataSourceManager
from spaceone.monitoring.manager.plugin_manager import PluginManager
from pprint import pprint
_LOGGER = logging.getLogger(__name__)
MAX_WORKER = 25
NUMBER_OF_MAX_PER_SERVICE_ACCOUNT = 30


@authentication_handler
@authorization_handler
@mutation_handler
@event_handler
class MetricService(BaseService):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.inventory_mgr: InventoryManager = self.locator.get_manager('InventoryManager')
        self.secret_mgr: SecretManager = self.locator.get_manager('SecretManager')
        self.data_source_mgr: DataSourceManager = self.locator.get_manager('DataSourceManager')
        self.plugin_mgr: PluginManager = self.locator.get_manager('PluginManager')

    @transaction(append_meta={'authorization.scope': 'DOMAIN'})
    @check_required(['data_source_id', 'resource_type', 'resources', 'domain_id'])
    def list(self, params):
        """ Get resource's metrics

        Args:
            params (dict): {
                'data_source_id': 'str',
                'resource_type': 'str',
                'resources': 'list',
                'domain_id': 'str'
            }

        Returns:
            metrics (list)
        """
        data_source_id = params['data_source_id']
        resource_type = params['resource_type']
        resources = params['resources']
        domain_id = params['domain_id']

        data_source_vo = self.data_source_mgr.get_data_source(data_source_id, domain_id)

        self._check_data_source_state(data_source_vo)

        plugin_metadata = data_source_vo.plugin_info.metadata
        plugin_options = data_source_vo.plugin_info.options
        required_keys = plugin_metadata.get('required_keys', [])

        plugin_id = data_source_vo.plugin_info.plugin_id
        version = data_source_vo.plugin_info.version

        self._check_resource_type(plugin_metadata, resource_type)
        self.plugin_mgr.initialize(plugin_id, version, domain_id)

        response = {
            'metrics': None,
            'available_resources': {},
            'domain_id': domain_id
        }
        metrics_dict = {}
        and_metric_keys = []

        for resource_id in resources:
            response['available_resources'][resource_id] = False

        resources_info = self.inventory_mgr.list_resources(resources, resource_type, required_keys, domain_id)

        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKER) as executor:
            future_executors = []

            for resource_id, resource_info in resources_info.items():

                concurrent_param = {'response': response,
                                    'resource_id': resource_id,
                                    'resource_info': resource_info,
                                    'plugin_options': plugin_options,
                                    'data_source_vo': data_source_vo,
                                    'domain_id': domain_id,
                                    'metrics_dict': metrics_dict,
                                    'and_metric_keys': and_metric_keys}

                future_executors.append(executor.submit(self.concurrent_secret_data_and_metrics_info, concurrent_param))

            for future in concurrent.futures.as_completed(future_executors):
                resource_id, metrics_dict, and_metric_keys = future.result()
                response['available_resources'][resource_id] = True

            _LOGGER.debug(f'[list] All metrics : {metrics_dict}')
            _LOGGER.debug(f'[list] And metric keys : {and_metric_keys}')

        response['metrics'] = self._intersect_metric_keys(metrics_dict, and_metric_keys)

        return response

    @transaction(append_meta={'authorization.scope': 'DOMAIN'})
    @check_required(['data_source_id', 'resource_type', 'resources', 'metric', 'start', 'end', 'domain_id'])
    def get_data(self, params):
        """ Get resource's metric data

        Args:
            params (dict): {
                'data_source_id': 'str',
                'resource_type': 'str',
                'resources': 'list',
                'metric': 'str',
                'start': 'str',
                'end': 'str',
                'period': 'int',
                'stat': 'str',
                'domain_id': 'str'
            }

        Returns:
            metric_data (list)
        """
        data_source_id = params['data_source_id']
        resource_type = params['resource_type']
        resources = params['resources']
        domain_id = params['domain_id']

        data_source_vo = self.data_source_mgr.get_data_source(data_source_id, domain_id)

        self._check_data_source_state(data_source_vo)

        plugin_metadata = data_source_vo.plugin_info.metadata
        plugin_options = data_source_vo.plugin_info.options
        required_keys = plugin_metadata.get('required_keys', [])

        plugin_id = data_source_vo.plugin_info.plugin_id
        version = data_source_vo.plugin_info.version

        self._check_resource_type(plugin_metadata, resource_type)

        self.plugin_mgr.initialize(plugin_id, version, domain_id)

        response = {
            'labels': None,
            'resource_values': {},
            'domain_id': domain_id
        }

        resources_info = self.inventory_mgr.list_resources(resources, resource_type, required_keys, domain_id)

        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKER) as executor:
            future_executors = []

            for resource_id, resource_info in resources_info.items():

                print('### data_source_vo ###')
                pprint(data_source_vo.to_dict())

                secret_data, schema = self._get_secret_data(resource_id, resource_info, data_source_vo, domain_id)

                concurrent_param = {'resource_id': resource_id,
                                    'schema': schema,
                                    'plugin_options': plugin_options,
                                    'secret_data': secret_data,
                                    'resource': resource_info,
                                    'metric': params['metric'],
                                    'start': params['start'],
                                    'end': params['end'],
                                    'period': params.get('period'),
                                    'stat': params.get('stat')}

                future_executors.append(executor.submit(self.concurrent_get_metric_data, concurrent_param))

            for future in concurrent.futures.as_completed(future_executors):
                resource_id, metric_data = future.result()

                if response['labels'] is None:
                    response['labels'] = metric_data.get('labels', [])

                response['resource_values'][resource_id] = metric_data.get('values', [])

        return response

    def concurrent_secret_data_and_metrics_info(self, param):

        resource_id = param.get('resource_id')
        resource_info = param.get('resource_info')
        data_source_vo = param.get('data_source_vo')
        domain_id = param.get('domain_id')
        plugin_options = param.get('plugin_options')
        metrics_dict = param.get('metrics_dict')
        and_metric_keys = param.get('and_metric_keys')
        metric_param = {}

        try:
            secret_data, schema = self._get_secret_data(resource_id, resource_info, data_source_vo, domain_id)
            metric_param.update({'secret_data': secret_data, 'schema': schema})
        except Exception as e:
            _LOGGER.error(f'[list] Get resource secret error ({resource_id}): {str(e)}',
                          extra={'traceback': traceback.format_exc()})

        try:
            metrics_info = self.plugin_mgr.list_metrics(metric_param.get('schema'),
                                                        plugin_options,
                                                        metric_param.get('secret_data'),
                                                        resource_info)
            metric_param.update({'metrics_info': metrics_info})

        except Exception as e:
            _LOGGER.error(f'[list] List metrics error ({resource_id}): {str(e)}',
                          extra={'traceback': traceback.format_exc()})

        metrics_dict, and_metric_keys = self._merge_metric_keys(metric_param.get('metrics_info'),
                                                                metrics_dict,
                                                                and_metric_keys)

        return resource_id, metrics_dict, and_metric_keys

    def concurrent_get_metric_data(self, param):
        metric_data_info = self.plugin_mgr.get_metric_data(param.get('schema'),
                                                           param.get('plugin_options'),
                                                           param.get('secret_data'),
                                                           param.get('resource'),
                                                           param.get('metric'),
                                                           param.get('start'),
                                                           param.get('end'),
                                                           param.get('period'),
                                                           param.get('stat'))
        return param.get('resource_id'), metric_data_info

    @staticmethod
    def _check_data_source_state(data_source_vo):
        if data_source_vo.state == 'DISABLED':
            raise ERROR_DATA_SOURCE_STATE_DISABLED(data_source_id=data_source_vo.data_source_id)

    @staticmethod
    def _check_resource_type(plugin_metadata, resource_type):
        supported_resource_type = plugin_metadata['supported_resource_type']

        if resource_type not in supported_resource_type:
            raise ERROR_NOT_SUPPORT_RESOURCE_TYPE(supported_resource_type=supported_resource_type)

    def _get_secret_data(self, resource_id, resource_info, data_source_vo, domain_id):
        use_resource_secret = data_source_vo.capability.get('use_resource_secret', False)
        supported_schema = data_source_vo.capability.get('supported_schema', [])

        if use_resource_secret:
            secret_filter = {
                'provider': data_source_vo.plugin_info['provider'],
                'supported_schema': supported_schema,
                'secrets': resource_info['collection_info']['secrets']
            }

            print('### secret_filter ###')
            pprint(secret_filter)
            print()
            print('resource_id')
            print(resource_id)

            return self.secret_mgr.get_resource_secret_data(resource_id, secret_filter, domain_id)

        else:
            secret_filter = {
                'secret_id': data_source_vo.plugin_info['secret_id'],
                'supported_schema': supported_schema
            }

            print('### secret_filter ###')
            pprint(secret_filter)
            print()
            print('resource_id')
            print(resource_id)

            return self.secret_mgr.get_plugin_secret_data(secret_filter, domain_id)

    @staticmethod
    def _intersect_metric_keys(metrics_dict, and_metric_keys):
        metrics = []
        for metric_key, metric_info in metrics_dict.items():
            if metric_key in and_metric_keys:
                metrics.append(metric_info)

        return metrics

    @staticmethod
    def _merge_metric_keys(metrics_info, metrics_dict, and_metric_keys):
        for metric_info in metrics_info.get('metrics', []):
            if 'key' in metric_info:
                metric_key = metric_info['key']

                if metric_key not in and_metric_keys:
                    metrics_dict[metric_key] = metric_info
                    and_metric_keys.append(metric_key)

        return metrics_dict, and_metric_keys


