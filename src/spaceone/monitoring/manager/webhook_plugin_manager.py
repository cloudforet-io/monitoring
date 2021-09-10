import logging

from spaceone.core.manager import BaseManager
from spaceone.monitoring.model.webhook_model import Webhook
from spaceone.monitoring.manager.plugin_manager import PluginManager
from spaceone.monitoring.connector.webhook_plugin_connector import WebhookPluginConnector

_LOGGER = logging.getLogger(__name__)


class WebhookPluginManager(BaseManager):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.wp_connector: WebhookPluginConnector = self.locator.get_connector('WebhookPluginConnector')

    def initialize(self, endpoint):
        _LOGGER.debug(f'[initialize] webhook plugin endpoint: {endpoint}')
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

    def get_webhook_plugin_endpoint_by_vo(self, webhook_vo: Webhook):
        plugin_info = webhook_vo.plugin_info.to_dict()
        endpoint, updated_version = self.get_webhook_plugin_endpoint(plugin_info, webhook_vo.domain_id)

        if updated_version:
            _LOGGER.debug(f'[get_webhook_plugin_endpoint_by_vo] upgrade plugin version: {plugin_info["version"]} -> {updated_version}')
            self.upgrade_webhook_plugin_version(webhook_vo, endpoint, updated_version)

        return endpoint

    def get_webhook_plugin_endpoint(self, plugin_info, domain_id):
        plugin_mgr: PluginManager = self.locator.get_manager('PluginManager')
        return plugin_mgr.get_plugin_endpoint(plugin_info, domain_id)

    def upgrade_webhook_plugin_version(self, webhook_vo: Webhook, endpoint, updated_version):
        plugin_info = webhook_vo.plugin_info.to_dict()
        self.initialize(endpoint)
        plugin_metadata = self.init_plugin(plugin_info.get('options', {}))
        plugin_info['version'] = updated_version
        plugin_info['metadata'] = plugin_metadata
        webhook_vo.update({'plugin_info': plugin_info})
