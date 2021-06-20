import logging

from spaceone.core.manager import BaseManager
from spaceone.core.connector.space_connector import SpaceConnector

_LOGGER = logging.getLogger(__name__)


class PluginManager(BaseManager):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.plugin_connector: SpaceConnector = self.locator.get_connector('SpaceConnector', service='plugin')

    def get_plugin_endpoint(self, plugin_id, version, domain_id):
        response = self.plugin_connector.dispatch('Plugin.get_plugin_endpoint', {
            'plugin_id': plugin_id,
            'version': version,
            'domain_id': domain_id
        })

        endpoint = response['endpoint']
        _LOGGER.debug(f'[get_plugin_endpoint] endpoint: {endpoint}')

        return endpoint
