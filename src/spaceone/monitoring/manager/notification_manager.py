import logging

from spaceone.core import config
from spaceone.core.connector.space_connector import SpaceConnector
from spaceone.core.manager import BaseManager

_LOGGER = logging.getLogger(__name__)


class NotificationManager(BaseManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.notification_connector: SpaceConnector = self.locator.get_connector(
            "SpaceConnector", service="notification", token=config.get_global("TOKEN")
        )

    def create_notification(self, message, domain_id):
        _LOGGER.debug(f"Notify message: {message}")
        system_token = config.get_global("TOKEN")
        return self.notification_connector.dispatch(
            "Notification.create", message, toke=system_token, x_domain_id=domain_id
        )
