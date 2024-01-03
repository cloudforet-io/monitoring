import logging

from spaceone.core.connector.space_connector import SpaceConnector
from spaceone.core.manager import BaseManager

_LOGGER = logging.getLogger(__name__)


class NotificationManager(BaseManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.notification_connector: SpaceConnector = self.locator.get_connector(
            "SpaceConnector", service="notification"
        )
        self.token_type = self.transaction.get_meta("authorization.token_type")

    def create_notification(self, message: dict, domain_id: str) -> dict:
        _LOGGER.debug(f"Notify message: {message}")
        if self.token_type == "SYSTEM_TOKEN":
            return self.notification_connector.dispatch(
                "Notification.create", message, x_domain_id=domain_id
            )
        else:
            return self.notification_connector.dispatch("Notification.create", message)
