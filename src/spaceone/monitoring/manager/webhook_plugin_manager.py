import logging

from spaceone.core.manager import BaseManager
from spaceone.monitoring.error import *
from spaceone.monitoring.connector.plugin_connector import PluginConnector
from spaceone.monitoring.connector.webhook_plugin_connector import WebhookPluginConnector

_LOGGER = logging.getLogger(__name__)


class WebhookPluginManager(BaseManager):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.plugin_connector: PluginConnector = self.locator.get_connector('PluginConnector')
        self.wp_connector: WebhookPluginConnector = self.locator.get_connector('WebhookPluginConnector')

    def initialize(self, plugin_id, version, domain_id):
        endpoint = self.plugin_connector.get_plugin_endpoint(plugin_id, version, domain_id)
        _LOGGER.debug(f'[init_plugin] endpoint: {endpoint}')
        self.wp_connector.initialize(endpoint)

    def init_plugin(self, options):
        plugin_info = self.wp_connector.init(options)

        _LOGGER.debug(f'[plugin_info] {plugin_info}')
        plugin_metadata = plugin_info.get('metadata', {})

        return plugin_metadata

    def verify_plugin(self, options):
        self.wp_connector.verify(options)

    def parse_event(self, options, data):
        return self.wp_connector.parse_event(options, data)
