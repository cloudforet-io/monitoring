import logging
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
    @check_required(['data_source_id', 'resources', 'domain_id'])
    def list(self, params):
        """ Get resource's metrics

        Args:
            params (dict): {
                'data_source_id': 'str',
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

        plugin_info = data_source_vo.plugin_info
        plugin_metadata = plugin_info.metadata
        self._check_plugin_metadata(plugin_metadata, params, data_source_id)
        self.plugin_initialize(data_source_vo)

        metrics_dict = {}
        and_metric_keys = []

        response = {
            'metrics': [],
            'available_resources': {},
            'domain_id': domain_id
        }

        for resource_id in resources:
            response['available_resources'][resource_id] = False

        required_keys = plugin_metadata.get('required_keys')
        cloud_services_info = self.inventory_mgr.list_resources(resources, required_keys, domain_id)

        list_metric_params = []
        for cloud_service_info in cloud_services_info:
            secret = self.secret_mgr.get_secret_from_resource(cloud_service_info, data_source_vo, domain_id)
            secret_data = self.secret_mgr.get_secret_data(secret['secret_id'], domain_id)
            query = self.get_query_from_cloud_service(cloud_service_info, plugin_info)

            list_metric_params.append({
                'schema': secret.get('schema'),
                'options': plugin_info.options,
                'secret_data': secret_data,
                'query': query,
                'cloud_service_id': cloud_service_info['cloud_service_id'],
                'data_source_vo': data_source_vo,
                'domain_id': domain_id,
                'metrics_dict': metrics_dict,
                'and_metric_keys': and_metric_keys
            })

        metric_responses = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT_WORKER) as executor:
            future_executors = []

            for _params in list_metric_params:
                future_executors.append(executor.submit(self.list_metrics_info, _params))

            for future in concurrent.futures.as_completed(future_executors):
                metric_responses.append(future.result())

        response = self._merge_metric(metric_responses, domain_id)
        return response

    @transaction(append_meta={'authorization.scope': 'DOMAIN'})
    @check_required(['data_source_id', 'metric_query', 'metric', 'start', 'end', 'domain_id'])
    def get_data(self, params):
        """ Get resource's metric data

        Args:
            params (dict): {
                'data_source_id': 'str',
                'metric_query': 'dict',
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
        metric_query = params['metric_query']
        domain_id = params['domain_id']

        data_source_vo = self.data_source_mgr.get_data_source(data_source_id, domain_id)
        self._check_data_source_state(data_source_vo)

        plugin_metadata = data_source_vo.plugin_info.metadata
        self._check_plugin_metadata(plugin_metadata, params, data_source_id)
        self.plugin_initialize(data_source_vo)

        response = {
            'labels': [],
            'values': {},
            'domain_id': domain_id
        }

        required_keys = plugin_metadata.get('required_keys')
        resource_ids = self.get_resource_ids_from_metric_query(metric_query)
        resources_info = self.inventory_mgr.list_resources(resource_ids, required_keys, domain_id)
        resources_chunks = self.list_chunk_resources(resources_info, metric_query, data_source_vo, domain_id)

        _LOGGER.debug(f"[get_data] chunk_resources: {resources_chunks}")

        metric_data_params = self.set_metric_data_params(params)

        for chunk_resources in resources_chunks.values():
            metric_data_params.update({
                'secret_data': chunk_resources.get('secret_data'),
                'metric_query': chunk_resources.get('metric_query'),
                'options': chunk_resources.get('options', {})
            })

            if 'schema' in chunk_resources:
                metric_data_params.update({'schema': chunk_resources.get('schema')})

            metric_data_response = self.get_metric_data(metric_data_params)

            if not response['labels'] and metric_data_response.get('labels', []):
                response['labels'] = metric_data_response['labels']

            if values := metric_data_response.get('values'):
                response['values'].update(values)

        return response

    def list_chunk_resources(self, resources, metric_query, data_source_vo, domain_id):
        """
        chunk_resources(dict): {
            'provider.region_code.secret_id.random_key': {
                'schema': 'str',
                'secret_data': 'dict',
                'region_name': 'str',
                'options': 'dict',
                'metric_query': 'dict'     # MAX_REQUEST_LIMIT
            },
            ...
        }
        """
        chunk_resources = {}
        provider = data_source_vo.plugin_info['provider']

        for resource in resources:
            cloud_service_id = resource['cloud_service_id']
            if cloud_service_id in metric_query:
                region_code = self.get_region_from_resource(resource)
                secret = self.secret_mgr.get_secret_from_resource(resource, data_source_vo, domain_id)
                chunk_key = self._generate_chunk_key(provider, region_code, secret['secret_id'])

                metric_query[cloud_service_id]['region_name'] = region_code
                chunk_resource = {cloud_service_id: metric_query[cloud_service_id]}

                if chunk_key in chunk_resources:
                    chunk_info = chunk_resources[chunk_key]

                    if 'region_name' not in chunk_info:
                        chunk_info.update({'region_name': region_code})

                    if 'secret_data' not in chunk_info:
                        chunk_info.update({'secret_data': self.secret_mgr.get_secret_data(secret['secret_id'], domain_id)})

                    if 'schema' not in chunk_info:
                        chunk_info.update({'schema': secret.get('schema')})

                    _metric_query = chunk_info['metric_query']

                    if len(_metric_query) >= MAX_REQUEST_LIMIT:
                        new_chunk_key = f'{chunk_key}.{random_string(1)}'
                        # move chunk to new key
                        chunk_resources[new_chunk_key] = chunk_info
                        # generate a new chunk
                        chunk_resources[chunk_key] = {
                            'region_name': region_code,
                            'secret_data': self.secret_mgr.get_secret_data(secret['secret_id'], domain_id),
                            'metric_query': chunk_resource,
                        }
                    else:
                        _metric_query[cloud_service_id] = metric_query[cloud_service_id]
                else:
                    # generate a new chunk
                    chunk_resources[chunk_key] = {
                        'region_name': region_code,
                        'secret_data': self.secret_mgr.get_secret_data(secret['secret_id'], domain_id),
                        'metric_query': chunk_resource,
                    }

        return chunk_resources

    def plugin_initialize(self, data_source_vo):
        endpoint = self.ds_plugin_mgr.get_data_source_plugin_endpoint_by_vo(data_source_vo)
        self.ds_plugin_mgr.initialize(endpoint)

    def get_metric_data(self, params):
        metric_data_info = {'labels': [], 'values': {}}

        try:
            metric_data_info = self.ds_plugin_mgr.get_metric_data(params)
        except Exception as e:
            print(e)

        return metric_data_info

    def list_metrics_info(self, params):
        schema = params.get('schema')
        secret_data = params['secret_data']
        cloud_service_id = params['cloud_service_id']
        query = params.get('query', {})
        options = params.get('options', {})

        try:
            metrics_info = self.ds_plugin_mgr.list_metrics(schema, options, secret_data, query)
            _LOGGER.debug(f'[list_metric_info] metrics_info: {metrics_info}')
            return {
                'metrics': metrics_info.get('metrics', []),
                'resource_id': cloud_service_id
            }
            # return response
        except Exception as e:
            _LOGGER.error(f'[list_metrics]: {e}')
            return {}

    def _merge_metric(self, metric_responses, domain_id):
        response = {
            'metrics': [],
            'available_resources': {},
            'domain_id': domain_id
        }

        available_resources, metric_responses, cloud_service_metric_set_info = self.set_preload_metric(metric_responses)

        _LOGGER.debug(f'available_resources: {available_resources}')
        _LOGGER.debug(f'metric_responses: {metric_responses}')
        _LOGGER.debug(f'cloud_service_metric_set_info: {cloud_service_metric_set_info}')

        if len(metric_responses) == 1:
            response['metrics'] = metric_responses[0]['metrics']
        elif len(metric_responses) > 1:
            _intersected_metric_keys = self._intersection_metric_keys(cloud_service_metric_set_info)

            response_metrics = []
            for metric_response in metric_responses:
                for _metric in metric_response['metrics']:
                    if _metric['key'] in _intersected_metric_keys:
                        match_key = False
                        for response_metric in response_metrics:
                            if response_metric['key'] == _metric['key']:
                                response_metric['metric_query'].update(_metric['metric_query'])
                                match_key = True
                                break

                        if match_key is False:
                            response_metrics.append(_metric)

            response['metrics'] = response_metrics

        response['available_resources'] = available_resources

        _LOGGER.debug(response)
        return response

    @staticmethod
    def set_preload_metric(metric_responses):
        available_resources = {}
        cloud_service_metric_set_info = {}

        for metric_response in metric_responses:
            if cloud_service_id := metric_response.get('resource_id'):
                available_resources[cloud_service_id] = True

                _metric_keys = []
                for _metric in metric_response['metrics']:
                    _metric_keys.append(_metric['key'])

                    _metric_query = _metric['metric_query']
                    _metric['metric_query'] = {cloud_service_id: _metric_query}

                cloud_service_metric_set_info[cloud_service_id] = _metric_keys

        return available_resources, metric_responses, cloud_service_metric_set_info

    @staticmethod
    def _intersection_metric_keys(cloud_service_metric_set_info):
        target_metrics = []

        for metrics in cloud_service_metric_set_info.values():
            if metrics and target_metrics:
                target_metrics = list(set(metrics) & set(target_metrics))

            if metrics and not target_metrics:
                target_metrics = metrics

        return target_metrics

    @staticmethod
    def get_resource_ids_from_metric_query(metric_query):
        return [resource_id for resource_id in metric_query.keys()]

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
        if 'supported_stat' in metadata and 'stat' in params:
            if params['stat'] not in metadata['supported_stat']:
                raise ERROR_NOT_SUPPORT_METRIC_STAT(stat=params['stat'])

        if 'required_keys' in metadata:
            if not metadata['required_keys']:
                raise ERROR_NOT_FOUND_REQUIRED_KEY(data_source_id=data_source_id)
        else:
            raise ERROR_NOT_FOUND_REQUIRED_KEY(data_source_id=data_source_id)

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

    @staticmethod
    def get_query_from_cloud_service(cloud_service_info, plugin_info):
        metadata = plugin_info.metadata
        required_keys = metadata.get('required_keys', [])

        if required_keys:
            query_key = required_keys[0]
            return get_dict_value(cloud_service_info, query_key, default_value={})
        else:
            raise ERROR_REQUIRED_KEYS_NOT_EXISTS(plugin_id=plugin_info.plugin_id)
