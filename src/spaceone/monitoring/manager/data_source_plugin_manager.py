import logging

from spaceone.core.manager import BaseManager
from spaceone.monitoring.error import *
from spaceone.monitoring.manager.plugin_manager import PluginManager
from spaceone.monitoring.connector.datasource_plugin_connector import DataSourcePluginConnector
from spaceone.monitoring.model.data_source_model import DataSource
from spaceone.monitoring.model.plugin_metadata_model import MetricPluginMetadataModel, LogPluginMetadataModel

_LOGGER = logging.getLogger(__name__)


class DataSourcePluginManager(BaseManager):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dsp_connector: DataSourcePluginConnector = self.locator.get_connector('DataSourcePluginConnector')

    def initialize(self, endpoint):
        _LOGGER.debug(f'[initialize] data source plugin endpoint: {endpoint}')
        self.dsp_connector.initialize(endpoint)

    def init_plugin(self, options, monitoring_type):
        plugin_info = self.dsp_connector.init(options)

        _LOGGER.debug(f'[plugin_info] {plugin_info}')
        plugin_metadata = plugin_info.get('metadata', {})

        self._validate_plugin_metadata(plugin_metadata, monitoring_type)

        return plugin_metadata

    def verify_plugin(self, options, secret_data, schema):
        self.dsp_connector.verify(options, secret_data, schema)

    def list_metrics(self, schema, options, secret_data, resource):
        return self.dsp_connector.list_metrics(schema, options, secret_data, resource)

    def get_metric_data(self, schema, options, secret_data, resource, *args):
        return self.dsp_connector.get_metric_data(schema, options, secret_data, resource, *args)

    def list_logs(self, schema, options, secret_data, resource, *args):
        response_stream = self.dsp_connector.list_logs(schema, options, secret_data, resource, *args)

        logs = []
        for result in self._process_stream(response_stream, return_resource_type='monitoring.Log'):
            logs += result.get('logs', [])

        return {
            'logs': logs
        }

    @staticmethod
    def _validate_plugin_metadata(plugin_metadata, monitoring_type):
        try:
            if monitoring_type == 'METRIC':
                MetricPluginMetadataModel(plugin_metadata).validate()
            else:
                LogPluginMetadataModel(plugin_metadata).validate()

        except Exception as e:
            raise ERROR_INVALID_PLUGIN_OPTIONS(reason=str(e))

    @staticmethod
    def _process_stream(response_stream, return_resource_type=None):
        is_resource_type_match = False
        for response in response_stream:
            if 'actions' in response:
                pass

            if return_resource_type and response.get('resource_type') == return_resource_type:
                if 'result' not in response:
                    raise ERROR_INTERNAL_API(message=f'Plugin response error: no return result')

                is_resource_type_match = True
                yield response['result']

        if return_resource_type is not None and is_resource_type_match is False:
            raise ERROR_INTERNAL_API(
                message=f'Plugin response error: no return resource_type ({return_resource_type})')

    def get_data_source_plugin_endpoint_by_vo(self, data_source_vo: DataSource):
        plugin_info = data_source_vo.plugin_info.to_dict()
        endpoint, updated_version = self.get_data_source_plugin_endpoint(plugin_info, data_source_vo.domain_id)

        if updated_version:
            _LOGGER.debug(f'[get_data_source_plugin_endpoint_by_vo] upgrade plugin version: {plugin_info["version"]} -> {updated_version}')
            self.upgrade_data_source_plugin_version(data_source_vo, endpoint, updated_version)

        return endpoint

    def get_data_source_plugin_endpoint(self, plugin_info, domain_id):
        plugin_mgr: PluginManager = self.locator.get_manager('PluginManager')
        return plugin_mgr.get_plugin_endpoint(plugin_info, domain_id)

    def upgrade_data_source_plugin_version(self, data_source_vo: DataSource, endpoint, updated_version):
        plugin_info = data_source_vo.plugin_info.to_dict()
        self.initialize(endpoint)
        plugin_metadata = self.init_plugin(plugin_info.get('options', {}), data_source_vo.monitoring_type)
        plugin_info['version'] = updated_version
        plugin_info['metadata'] = plugin_metadata
        data_source_vo.update({'plugin_info': plugin_info})
