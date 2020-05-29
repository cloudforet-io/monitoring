import logging
import traceback
from spaceone.core.service import *

from spaceone.monitoring.error import *
from spaceone.monitoring.manager.inventory_manager import InventoryManager
from spaceone.monitoring.manager.secret_manager import SecretManager
from spaceone.monitoring.manager.data_source_manager import DataSourceManager
from spaceone.monitoring.manager.plugin_manager import PluginManager

_LOGGER = logging.getLogger(__name__)


@authentication_handler
@authorization_handler
@event_handler
class MetricService(BaseService):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.inventory_mgr: InventoryManager = self.locator.get_manager('InventoryManager')
        self.secret_mgr: SecretManager = self.locator.get_manager('SecretManager')
        self.data_source_mgr: DataSourceManager = self.locator.get_manager('DataSourceManager')
        self.plugin_mgr: PluginManager = self.locator.get_manager('PluginManager')

    @transaction
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

        plugin_options = data_source_vo.plugin_info.options
        reference_keys = plugin_options.get('reference_keys', [])
        plugin_id = data_source_vo.plugin_info.plugin_id
        version = data_source_vo.plugin_info.version

        self._check_resource_type(plugin_options, resource_type)

        self.plugin_mgr.init_plugin(plugin_id, version, domain_id)

        response = {
            'metrics': None,
            'available_resources': {},
            'domain_id': domain_id
        }
        metrics_dict = {}
        and_metric_keys = []

        for resource_id in resources:
            response['available_resources'][resource_id] = False

        resources_info = self.inventory_mgr.list_resources(resources, resource_type, reference_keys, domain_id)

        for resource_id, resource_info in resources_info.items():
            try:
                resource_key = self.inventory_mgr.get_resource_key(resource_type, resource_info, reference_keys)
            except Exception as e:
                _LOGGER.error(f'[list] Get resource reference error ({resource_id}): {str(e)}',
                              extra={'traceback': traceback.format_exc()})
                continue

            _LOGGER.debug(f'[list] Resource info : resource_id = {resource_id} / resource_key = {resource_key}')

            try:
                secret_data = self._get_secret_data(resource_id, resource_info, data_source_vo, domain_id)
            except Exception as e:
                _LOGGER.error(f'[list] Get resource secret error ({resource_id}): {str(e)}',
                              extra={'traceback': traceback.format_exc()})
                continue

            try:
                metrics_info = self.plugin_mgr.list_metrics(plugin_options, secret_data, resource_key)

            except Exception as e:
                _LOGGER.error(f'[list] List metrics error ({resource_id}): {str(e)}',
                              extra={'traceback': traceback.format_exc()})
                continue

            metrics_dict, and_metric_keys = self._merge_metric_keys(metrics_info, metrics_dict, and_metric_keys)
            response['available_resources'][resource_id] = True

        _LOGGER.debug(f'[list] All metrics : {metrics_dict}')
        _LOGGER.debug(f'[list] And metric keys : {and_metric_keys}')

        response['metrics'] = self._intersect_metric_keys(metrics_dict, and_metric_keys)
        return response

    @transaction
    @check_required(['data_source_id', 'resource_type', 'resources', 'metric', 'start', 'end', 'domain_id'])
    @change_timestamp_value(['start', 'end'], timestamp_format='iso8601')
    def get_data(self, params):
        """ Get resource's metric data

        Args:
            params (dict): {
                'data_source_id': 'str',
                'resource_type': 'str',
                'resources': 'list',
                'metric': 'str',
                'start': 'timestamp',
                'end': 'timestamp',
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

        plugin_options = data_source_vo.plugin_info.options
        reference_keys = plugin_options.get('reference_keys', [])
        plugin_id = data_source_vo.plugin_info.plugin_id
        version = data_source_vo.plugin_info.version

        self._check_resource_type(plugin_options, resource_type)

        self.plugin_mgr.init_plugin(plugin_id, version, domain_id)

        response = {
            'labels': None,
            'resource_values': {},
            'domain_id': domain_id
        }

        resources_info = self.inventory_mgr.list_resources(resources, resource_type, reference_keys, domain_id)

        for resource_id, resource_info in resources_info.items():
            resource_key = self.inventory_mgr.get_resource_key(resource_type, resource_info, reference_keys)

            secret_data = self._get_secret_data(resource_id, resource_info, data_source_vo, domain_id)
            metric_data_info = self.plugin_mgr.get_metric_data(plugin_options, secret_data, resource_key,
                                                               params['metric'], params['start'], params['end'],
                                                               params.get('period'), params.get('stat'))

            if response['labels'] is None:
                response['labels'] = metric_data_info.get('labels', [])

            response['resource_values'][resource_id] = metric_data_info.get('values', [])

        return response

    @staticmethod
    def _check_data_source_state(data_source_vo):
        if data_source_vo.state == 'DISABLED':
            raise ERROR_DATA_SOURCE_STATE_DISABLED(data_source_id=data_source_vo.data_source_id)

    @staticmethod
    def _check_resource_type(plugin_options, resource_type):
        supported_resource_type = plugin_options['supported_resource_type']

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
