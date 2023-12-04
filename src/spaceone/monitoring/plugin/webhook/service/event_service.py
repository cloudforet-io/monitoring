import logging
from typing import List
from spaceone.core.service import BaseService, transaction, convert_model, check_required
from spaceone.monitoring.plugin.webhook.model.event_request import EventRequest
from spaceone.monitoring.plugin.webhook.model.event_response import EventResponse

_LOGGER = logging.getLogger(__name__)


class EventService(BaseService):

    @transaction
    @convert_model
    @check_required(['options', 'data'])
    def parse(self, params: EventRequest) -> List[EventResponse]:
        """ Persing Event Webhook

        Args:
            params (EventRequest): {
                'options': 'dict',
                'data': 'dict'
            }

        Returns:
            List[EventResponse]
        """
        func = self.get_plugin_method('parse')
        return func(params.dict())

