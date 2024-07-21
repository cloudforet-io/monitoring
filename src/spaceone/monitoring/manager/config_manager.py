import logging
from spaceone.core import config

from spaceone.core.connector.space_connector import SpaceConnector
from spaceone.core.manager import BaseManager

_LOGGER = logging.getLogger(__name__)


class ConfigManager(BaseManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config_connector: SpaceConnector = self.locator.get_connector(
            "SpaceConnector", service="config"
        )

    def get_domain_config(self, name: str, domain_id: str):
        system_token = config.get_global("TOKEN")

        return self.config_connector.dispatch(
            "DomainConfig.get",
            {"name": name},
            x_domain_id=domain_id,
            token=system_token,
        )
