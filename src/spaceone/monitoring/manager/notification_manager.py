import logging

from spaceone.core.auth.jwt.jwt_util import JWTUtil
from spaceone.core.connector.space_connector import SpaceConnector
from spaceone.core.manager import BaseManager

_LOGGER = logging.getLogger(__name__)


class NotificationManager(BaseManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        token = self.transaction.get_meta("token")
        self.token_type = JWTUtil.get_value_from_token(token, "typ")
        self.notification_connector: SpaceConnector = self.locator.get_connector(
            "SpaceConnector", service="notification"
        )

    def create_notification(self, message: dict, domain_id: str) -> dict:
        _LOGGER.debug(f"Notify message: {message}")
        if self.token_type == "SYSTEM_TOKEN":
            return self.notification_connector.dispatch(
                "Notification.create", message, x_domain_id=domain_id
            )
        else:
            return self.notification_connector.dispatch("Notification.create", message)
