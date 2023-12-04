import logging
from typing import Union
from spaceone.core.service import BaseService, transaction, convert_model, check_required
from spaceone.monitoring.plugin.webhook.model.webhook_request import WebhookRequest
from spaceone.monitoring.plugin.webhook.model.webhook_response import WebhookResponse

_LOGGER = logging.getLogger(__name__)


class WebhookService(BaseService):

    @transaction
    @convert_model
    @check_required(['options'])
    def init(self, params: WebhookRequest) -> Union[dict, WebhookResponse]:
        """ init plugin by options

        :param params (WebhookReauest): {
            'options': 'dict'   # Required
        }

        :return:
            WebhookResponse: {
                'metadata': 'dict'
            }
        """

        func = self.get_plugin_method('init')
        response = func(params.dict())
        return WebhookResponse(**response)

    @transaction
    @convert_model
    @check_required(['options'])
    def verify(self, params: WebhookRequest) -> None:
        """ verifying plugin

        :param params (WebhookRequest): {
                'options': 'dict'   # Request
            }

        :return:
            None
        """

        func = self.get_plugin_method('verify')
        func(params.dict())
