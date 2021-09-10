import logging

from spaceone.core.manager import BaseManager
from spaceone.core.connector.space_connector import SpaceConnector

_LOGGER = logging.getLogger(__name__)


class PluginManager(BaseManager):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.plugin_connector: SpaceConnector = self.locator.get_connector('SpaceConnector', service='plugin')

    def get_plugin_endpoint(self, plugin_info, domain_id):
        plugin_connector: SpaceConnector = self.locator.get_connector('SpaceConnector', service='plugin')
        response = plugin_connector.dispatch(
            'Plugin.get_plugin_endpoint',
            {
                'plugin_id': plugin_info['plugin_id'],
                'version': plugin_info.get('version'),
                'upgrade_mode': plugin_info.get('upgrade_mode', 'AUTO'),
                'domain_id': domain_id
            }
        )

        return response['endpoint'], response.get('updated_version')
