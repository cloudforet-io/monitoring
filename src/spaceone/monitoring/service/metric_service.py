import logging
import traceback
import time
import concurrent.futures
from spaceone.core.service import *

from spaceone.monitoring.error import *
from spaceone.monitoring.manager.inventory_manager import InventoryManager
from spaceone.monitoring.manager.secret_manager import SecretManager
from spaceone.monitoring.manager.data_source_manager import DataSourceManager
from spaceone.monitoring.manager.data_source_plugin_manager import DataSourcePluginManager

_LOGGER = logging.getLogger(__name__)
MAX_CONCURRENT_WORKER = [10, 5]

MAX_REQUEST_LIMIT = {
    'aws': 200,
    'google_cloud': 100,
    'azure': 10
}

MONITORING_PATH = {
    'aws': 'cloudwatch',
    'google_cloud': 'stackdriver',
    'azure': 'azure_monitor'
}


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
        self.ds_plugin_mgr: DataSourcePluginManager = self.locator.get_manager('DataSourcePluginManager')

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
        required_keys = plugin_metadata.get('required_keys', [])

        data_source_dict = data_source_vo.to_dict()
        plugin_info = data_source_dict['plugin_info']

        self._check_resource_type(plugin_metadata, resource_type)
        endpoint = self.ds_plugin_mgr.get_data_source_plugin_endpoint_by_vo(data_source_vo)
        self.ds_plugin_mgr.initialize(endpoint)

        response = {
            'metrics': None,
            'available_resources': {},
            'domain_id': domain_id
        }
        metrics_dict = {}
        and_metric_keys = []
        start_time = time.time()
        for resource_id in resources:
            response['available_resources'][resource_id] = False

        resources_info = self.inventory_mgr.list_resources(resource_type, resources, required_keys, domain_id)

        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT_WORKER[0]) as executor:
            future_executors = []

            for resource_id, resource_info in resources_info.items():
                concurrent_param = {'response': response,
                                    'resource_id': resource_id,
                                    'resource_info': resource_info,
                                    'plugin_metadata': plugin_metadata,
                                    'data_source_vo': data_source_vo,
                                    'domain_id': domain_id,
                                    'metrics_dict': metrics_dict,
                                    'and_metric_keys': and_metric_keys}

                future_executors.append(executor.submit(self.concurrent_secret_data_and_metrics_info, concurrent_param))

            print(f'** Before Create Thread {time.time() - start_time} Seconds **')

            for future in concurrent.futures.as_completed(future_executors):
                is_invalid, resource_id, metrics_dict, and_metric_keys = future.result()

                if not is_invalid:
                    response['available_resources'][resource_id] = True

            print(f'** After running Thread {time.time() - start_time} Seconds **')

            _LOGGER.debug(f'[list] All metrics : {metrics_dict}')
            _LOGGER.debug(f'[list] And metric keys : {and_metric_keys}')

        response['metrics'] = self._intersect_metric_keys(metrics_dict, and_metric_keys)

        print(f'** Get metric list  {time.time() - start_time} Seconds **')
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
        start_time = time.time()
        _metric = params['metric']
        concurrent_param = {'metric': params['metric'],
                            'start': params['start'],
                            'end': params['end'],
                            'period': params.get('period'),
                            'stat': params.get('stat')}

        data_source_vo = self.data_source_mgr.get_data_source(data_source_id, domain_id)

        self._check_data_source_state(data_source_vo)

        plugin_metadata = data_source_vo.plugin_info.metadata
        required_keys = plugin_metadata.get('required_keys', [])

        data_source_dict = data_source_vo.to_dict()
        plugin_info = data_source_dict['plugin_info']

        self._check_resource_type(plugin_metadata, resource_type)
        endpoint = self.ds_plugin_mgr.get_data_source_plugin_endpoint_by_vo(data_source_vo)
        self.ds_plugin_mgr.initialize(endpoint)

        response = {
            'labels': [],
            'resource_values': {},
            'domain_id': domain_id
        }

        resources_info = self.inventory_mgr.list_resources(resource_type, resources, required_keys, domain_id)
        filtered_resources = self.get_filtered_resources_info(resources_info, data_source_vo, domain_id)

        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT_WORKER[1]) as executor:
            future_executors = []
            print()
            print(f'** {_metric} :Before running Thread {time.time() - start_time} Seconds **')
            for filtered_resource in filtered_resources:
                concurrent_param.update({'schema': filtered_resource.get('schema'),
                                         'plugin_metadata': plugin_metadata,
                                         'secret_data': filtered_resource.get('secret_data'),
                                         'resources': filtered_resource})

                future_executors.append(executor.submit(self.concurrent_get_metric_data, concurrent_param))

            print(f'** {_metric} :After running Thread {time.time() - start_time} Seconds **')
            for future in concurrent.futures.as_completed(future_executors):
                metric_data = future.result()
                print(f'** Single Thread {time.time() - start_time} Seconds **')
                if not response.get('labels') and metric_data.get('labels', []):
                    response['labels'] = metric_data.get('labels', [])

                if metric_data.get('resource_values', {}) != {}:
                    response['resource_values'].update(metric_data.get('resource_values'))

        print(f'** Running Thread for {_metric} All has finished {time.time() - start_time} Seconds **')
        print()
        return response

    def get_filtered_resources_info(self, resources_info, data_source_vo, domain_id):
        filter_resources = []

        for resource_id, resource_info in resources_info.items():

            provider = data_source_vo.plugin_info['provider']

            if provider not in MONITORING_PATH.keys():
                raise ERROR_NOT_SUPPORT_PROVIDER_MONITORING(provider=provider)

            monitor_info_per_provider = resource_info.get('data', {}).get(MONITORING_PATH.get(provider))
            resource_key = 'sp_resource_id' if provider == 'azure' else 'resource_id'

            # Skip item, if selected items does not identical provider
            need_skip = False

            try:
                monitor_info_per_provider.update({resource_key: resource_id})
            except Exception as e:
                need_skip = True

            try:
                secret_data, schema = self._get_secret_data(resource_id, resource_info, data_source_vo, domain_id)
            except Exception as e:
                need_skip = True
                _LOGGER.error(f'[list] Get resource secret error ({resource_id}): {str(e)}', extra={'traceback': traceback.format_exc()})

            if not need_skip:
                index = None
                if provider == 'aws':
                    index = self._get_idx_by_value(provider, filter_resources, secret_data, schema,
                                                   monitor_info_per_provider.get('region_name'))
                elif provider == 'google_cloud':
                    index = self._get_idx_by_value(provider, filter_resources, secret_data, schema, None)

                elif provider == 'azure':
                    index = self._get_idx_by_value(provider, filter_resources, secret_data, schema, None)

                if index is None:
                    raise ERROR_NOT_MATCHING_RESOURCES(monitoring=monitor_info_per_provider)

                if index == -1:
                    attaching_resource = {
                        'secret_data': secret_data,
                        'schema': schema,
                        'resources': [monitor_info_per_provider]
                    }

                    if provider == 'aws':
                        attaching_resource.update({'region_name': monitor_info_per_provider.get('region_name')})

                    filter_resources.append(attaching_resource)

                else:
                    updatable = filter_resources[index].get('resources')
                    if updatable is not None:
                        filter_resources[index]['resources'].append(monitor_info_per_provider)

        return filter_resources

    def concurrent_get_metric_data(self, param):
        metric_data_info = {'labels': [],
                            'resource_values': {}}

        try:
            metric_data_info = self.ds_plugin_mgr.get_metric_data(param.get('schema'),
                                                                  param.get('plugin_metadata'),
                                                                  param.get('secret_data'),
                                                                  param.get('resources'),
                                                                  param.get('metric'),
                                                                  param.get('start'),
                                                                  param.get('end'),
                                                                  param.get('period'),
                                                                  param.get('stat'))

        except Exception as e:
            print(e)

        return metric_data_info

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

            return self.secret_mgr.get_resource_secret_data(resource_id, secret_filter, domain_id)

        else:
            secret_filter = {
                'secret_id': data_source_vo.plugin_info['secret_id'],
                'supported_schema': supported_schema
            }

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

    @staticmethod
    def _get_idx_by_value(provider, filter_resources, secret_data, schema, region_name):
        idx_list = []
        if provider == 'aws':
            idx_list = [index for (index, d) in enumerate(filter_resources) if
                        d.get('secret_data') == secret_data and d.get('schema') == schema and d.get(
                            'region_name') == region_name]

        elif provider == 'google_cloud':
            idx_list = [index for (index, d) in enumerate(filter_resources) if
                        d.get('secret_data') == secret_data and d.get('schema') == schema]

        elif provider == 'azure':
            idx_list = [index for (index, d) in enumerate(filter_resources) if
                        d.get('secret_data') == secret_data and d.get('schema') == schema]

        if not idx_list:
            return -1
        else:
            l_digit = len(idx_list) - 1
            prop_resource_list = filter_resources[idx_list[l_digit]].get('resources', [])
            return -1 if len(prop_resource_list) > MAX_REQUEST_LIMIT[provider] else idx_list[l_digit]

    def concurrent_secret_data_and_metrics_info(self, param):

        resource_id = param.get('resource_id')
        resource_info = param.get('resource_info')
        data_source_vo = param.get('data_source_vo')
        domain_id = param.get('domain_id')
        plugin_metadata = param.get('plugin_metadata')
        metrics_dict = param.get('metrics_dict')
        and_metric_keys = param.get('and_metric_keys')
        metric_param = {}
        is_invalid = False

        if not is_invalid:
            try:

                secret_data, schema = self._get_secret_data(resource_id, resource_info, data_source_vo, domain_id)
                metric_param.update({'secret_data': secret_data, 'schema': schema})

            except Exception as e:
                _LOGGER.error(f'[list] Get resource secret error ({resource_id}): {str(e)}',
                              extra={'traceback': traceback.format_exc()})

                is_invalid = True

        if not is_invalid:
            try:
                metrics_info = self.ds_plugin_mgr.list_metrics(metric_param.get('schema'),
                                                               plugin_metadata,
                                                               metric_param.get('secret_data'),
                                                               resource_info)

                metric_param.update({'metrics_info': metrics_info})

            except Exception as e:
                _LOGGER.error(f'[list] List metrics error ({resource_id}): {str(e)}',
                              extra={'traceback': traceback.format_exc()})
                is_invalid = True

        if not is_invalid:
            metrics_dict, and_metric_keys = self._merge_metric_keys(metric_param.get('metrics_info'),
                                                                    metrics_dict,
                                                                    and_metric_keys)

        return is_invalid, resource_id, metrics_dict, and_metric_keys
