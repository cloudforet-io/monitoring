import logging
import traceback
import concurrent.futures
from spaceone.core.service import *
from spaceone.core.utils import get_dict_value, random_string

from spaceone.monitoring.error import *
from spaceone.monitoring.manager.inventory_manager import InventoryManager
from spaceone.monitoring.manager.secret_manager import SecretManager
from spaceone.monitoring.manager.data_source_manager import DataSourceManager
from spaceone.monitoring.manager.data_source_plugin_manager import DataSourcePluginManager
from spaceone.monitoring.conf.global_conf import *

_LOGGER = logging.getLogger(__name__)


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
        resources = params['resources']
        domain_id = params['domain_id']

        data_source_vo = self.data_source_mgr.get_data_source(data_source_id, domain_id)
        self._check_data_source_state(data_source_vo)

        plugin_metadata = data_source_vo.plugin_info.metadata
        self._check_plugin_metadata(plugin_metadata, params, data_source_id)
        self.plugin_initialize(data_source_vo)

        response = {
            'metrics': None,
            'available_resources': {},
            'domain_id': domain_id
        }

        metrics_dict = {}
        and_metric_keys = []

        for resource_id in resources:
            response['available_resources'][resource_id] = False

        required_keys = plugin_metadata.get('required_keys')
        resources_info = self.inventory_mgr.list_resources(resources, required_keys, domain_id)

        list_metric_params = []
        for resource in resources_info:
            secret = self.get_secret(resource.get('collection_info', {}).get('secrets', []),
                                     data_source_vo, domain_id)
            secret_data = self.get_secret_data(secret['secret_id'], domain_id)

            list_metric_params.append({
                'schema': secret.get('schema'),
                'secret_data': secret_data,
                'resource_info': resource,
                'data_source_vo': data_source_vo,
                'domain_id': domain_id,
                'metrics_dict': metrics_dict,
                'and_metric_keys': and_metric_keys
            })

        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT_WORKER) as executor:
            future_executors = []

            for _params in list_metric_params:
                future_executors.append(executor.submit(self.list_metrics_info, _params))

            for future in concurrent.futures.as_completed(future_executors):
                metric_response = future.result()

                if resource_id := metric_response.get('resource_id'):
                    response['available_resources'][resource_id] = True

        response['metrics'] = self._intersect_metric_keys(metric_response["metrics_dict"],
                                                          metric_response["and_metric_keys"])

        _LOGGER.debug(f"[list] response: {response}")

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
        resources = params['resources']
        domain_id = params['domain_id']

        data_source_vo = self.data_source_mgr.get_data_source(data_source_id, domain_id)
        self._check_data_source_state(data_source_vo)

        plugin_metadata = data_source_vo.plugin_info.metadata
        self._check_plugin_metadata(plugin_metadata, params, data_source_id)

        self.plugin_initialize(data_source_vo)

        response = {
            'labels': [],
            'resource_values': {},
            'domain_id': domain_id
        }

        required_keys = plugin_metadata.get('required_keys')
        resources_info = self.inventory_mgr.list_resources(resources, required_keys, domain_id)
        resources_chunks = self.list_chunk_resources(resources_info, data_source_vo, required_keys[0], domain_id)

        _LOGGER.debug(f"[get_data] chunk_resources: {resources_chunks}")

        metric_data_params = self.set_metric_data_params(params)

        for chunk_resources in resources_chunks.values():

            metric_data_params.update({
                'secret_data': chunk_resources.get('secret_data'),
                'resource': {
                    'region_name': chunk_resources.get('region_name'),
                    'resources': chunk_resources.get('resources')
                }
            })

            metric_data_response = self.get_metric_data(metric_data_params)

            if not response['labels'] and metric_data_response.get('labels', []):
                response['labels'] = metric_data_response['labels']

            if resource_values := metric_data_response.get('resource_values'):
                response['resource_values'].update(resource_values)

        _LOGGER.debug(f"[get_data] response: {response}")
        return response

    def list_chunk_resources(self, resources, data_source_vo, required_keys, domain_id):
        """
        chunk_resources(dict): {
            'provider.region_code.account.random_key': {
                'secret_data': 'dict',
                'region_name': 'str',
                'resources': 'list'     # MAX_REQUEST_LIMIT
            },
            ...
        }
        """
        chunk_resources = {}
        provider = data_source_vo.plugin_info['provider']

        for resource in resources:
            region_code = self.get_region_from_resource(resource)
            secret = self.get_secret(resource.get('collection_info', {}).get('secrets', []),
                                     data_source_vo, domain_id)
            chunk_key = self._generate_chunk_key(provider, region_code, secret['secret_id'])
            chunk_resource = {
                'resource_id': resource['cloud_service_id'],
                'monitoring_info': get_dict_value(resource, required_keys)
            }

            if chunk_key in chunk_resources:
                chunk_info = chunk_resources[chunk_key]

                if 'region_name' not in chunk_info:
                    chunk_info.update({'region_name': region_code})

                if 'secret_data' not in chunk_info:
                    chunk_info.update({'secret_data': self.get_secret_data(secret['secret_id'], domain_id)})

                _resources = chunk_info.get('resources', [])

                if len(_resources) >= MAX_REQUEST_LIMIT:
                    new_chunk_key = f'{chunk_key}.{random_string(1)}'
                    chunk_resources[new_chunk_key] = chunk_info
                    chunk_resources[chunk_key] = {
                        'region_name': region_code,
                        'secret_data': self.get_secret_data(secret['secret_id'], domain_id),
                        'resources': [chunk_resource],
                    }
                else:
                    _resources.append(chunk_resource)
            else:
                # generate a new chunk
                chunk_resources[chunk_key] = {
                    'region_name': region_code,
                    'secret_data': self.get_secret_data(secret['secret_id'], domain_id),
                    'resources': [chunk_resource],
                }

        return chunk_resources

    def plugin_initialize(self, data_source_vo):
        endpoint = self.ds_plugin_mgr.get_data_source_plugin_endpoint_by_vo(data_source_vo)
        self.ds_plugin_mgr.initialize(endpoint)

    def get_metric_data(self, param):
        metric_data_info = {'labels': [], 'resource_values': {}}

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

    def get_secret(self, resource_secrets, data_source_vo, domain_id):
        secret = None

        if data_source_vo.capability.get('use_resource_secret', False):
            secret_filter = {
                'provider': data_source_vo.plugin_info.provider,
                'supported_schema': data_source_vo.capability.get('supported_schema', []),
                'secrets': resource_secrets
            }
            secret = self.secret_mgr.list_secrets_from_query(secret_filter, domain_id)[0]

        return secret

    def get_secret_data(self, secret_id, domain_id):
        return self.secret_mgr.get_secret_data(secret_id, domain_id)

    def list_metrics_info(self, params):
        schema = params.get('schema')
        resource_info = params.get('resource_info')
        secret_data = params.get('secret_data')
        metrics_dict = params.get('metrics_dict')
        and_metric_keys = params.get('and_metric_keys')
        options = {}

        try:
            metrics_info = self.ds_plugin_mgr.list_metrics(schema, options, secret_data, resource_info)
            response = self._merge_metric_keys(metrics_info, metrics_dict, and_metric_keys)
            response.update({'resource_id': resource_info.get('cloud_service_id')})
            return response
        except Exception as e:
            _LOGGER.error(f'[list_metrics]: {e}')
            return {}

    @staticmethod
    def set_metric_data_params(params):
        return_params = {
            'metric': params['metric'],
            'start': params['start'],
            'end': params['end'],
        }

        if 'period' in params:
            return_params['period'] = params['period']

        if 'stat' in params:
            return_params['stat'] = params['stat']

        return return_params

    @staticmethod
    def _generate_chunk_key(provider, region_code, secret_id):
        return f"{provider}.{region_code}.{secret_id}"

    @staticmethod
    def get_region_from_resource(resource):
        return resource.get('region_code', '')

    @staticmethod
    def get_account_from_resource(resource):
        return resource.get('account', '')

    @staticmethod
    def _check_data_source_state(data_source_vo):
        if data_source_vo.state == 'DISABLED':
            raise ERROR_DATA_SOURCE_STATE_DISABLED(data_source_id=data_source_vo.data_source_id)

    @staticmethod
    def _check_resource_type(plugin_metadata, resource_type):
        supported_resource_type = plugin_metadata['supported_resource_type']

        if resource_type not in supported_resource_type:
            raise ERROR_NOT_SUPPORT_RESOURCE_TYPE(supported_resource_type=supported_resource_type)

    @staticmethod
    def _check_plugin_metadata(metadata, params, data_source_id):
        if 'supported_resource_type' in metadata:
            if params['resource_type'] not in metadata['supported_resource_type']:
                raise ERROR_NOT_SUPPORT_RESOURCE_TYPE(resource_type=params['resource_type'])

        if 'supported_stat' in metadata and 'stat' in params:
            if params['stat'] not in metadata['supported_stat']:
                raise ERROR_NOT_SUPPORT_METRIC_STAT(stat=params['stat'])

        if 'required_keys' in metadata:
            if not metadata['required_keys']:
                raise ERROR_NOT_FOUND_REQUIRED_KEY(data_source_id=data_source_id)
        else:
            raise ERROR_NOT_FOUND_REQUIRED_KEY(data_source_id=data_source_id)

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

        return {'metrics_dict': metrics_dict, 'and_metric_keys': and_metric_keys}

    @staticmethod
    def get_required_key(metadata):
        required_keys = metadata.get('required_keys', [])

        if not required_keys:
            raise

        return required_keys[0]