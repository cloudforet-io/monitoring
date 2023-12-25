import logging

from spaceone.core import config
from spaceone.core.connector.space_connector import SpaceConnector
from spaceone.core.manager import BaseManager

_LOGGER = logging.getLogger(__name__)


class NotificationManager(BaseManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.notification_connector: SpaceConnector = self.locator.get_connector(
            "SpaceConnector", service="notification"
        )

    def create_notification(self, message: dict, domain_id: str) -> dict:
        _LOGGER.debug(f"Notify message: {message}")
        system_token = config.get_global("TOKEN")
        return self.notification_connector.dispatch(
            "Notification.create",
            message,
            token=system_token,
            x_domain_id=domain_id,
        )
