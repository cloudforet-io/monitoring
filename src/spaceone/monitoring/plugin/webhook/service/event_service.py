import logging
from typing import Union
from spaceone.core.service import (
    BaseService,
    transaction,
    convert_model,
    change_timestamp_value,
)
from spaceone.monitoring.plugin.webhook.model.event.request import EventParseRequest
from spaceone.monitoring.plugin.webhook.model.event.response import EventsResponse

_LOGGER = logging.getLogger(__name__)


class EventService(BaseService):
    @transaction
    @convert_model
    def parse(self, params: EventParseRequest) -> Union[EventsResponse, dict]:
        """Parsing Event Webhook

        Args:
            params (EventRequest): {
                'options': 'dict',
                'data': 'dict'
            }

        Returns:
            Union[EventResponse, dict]
        """
        func = self.get_plugin_method("parse")
        return func(params.dict())
