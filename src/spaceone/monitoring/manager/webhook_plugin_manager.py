import logging

from spaceone.core.connector.space_connector import SpaceConnector
from spaceone.core.manager import BaseManager

_LOGGER = logging.getLogger(__name__)


class WebhookPluginManager(BaseManager):
    def init_plugin(self, endpoint, options):
        plugin_connector: SpaceConnector = self.locator.get_connector(
            "SpaceConnector", endpoint=endpoint, token="NO_TOKEN"
        )
        return plugin_connector.dispatch("Webhook.init", {"options": options})

    def verify_plugin(self, endpoint, options):
        plugin_connector: SpaceConnector = self.locator.get_connector(
            "SpaceConnector", endpoint=endpoint, token="NO_TOKEN"
        )
        plugin_connector.dispatch("Webhook.verify", {"options": options})

    def parse_event(self, endpoint, options, data):
        plugin_connector: SpaceConnector = self.locator.get_connector(
            "SpaceConnector", endpoint=endpoint, token="NO_TOKEN"
        )

        params = {
            "options": options,
            "data": data,
        }

        return plugin_connector.dispatch("Event.parse", params)
