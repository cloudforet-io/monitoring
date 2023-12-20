import logging
from typing import Union
from spaceone.core.service import BaseService, transaction, convert_model
from spaceone.monitoring.plugin.webhook.model.webhook.request import (
    WebhookInitRequest,
    WebhookVerityRequest,
)
from spaceone.monitoring.plugin.webhook.model.webhook.response import WebhookResponse

_LOGGER = logging.getLogger(__name__)


class WebhookService(BaseService):
    @transaction
    @convert_model
    def init(self, params: WebhookInitRequest) -> Union[dict, WebhookResponse]:
        """init plugin by options

        :param params: WebhookRequest: {
            'options': 'dict'   # Required
        }

        :return:
            WebhookResponse: {
                'metadata': 'dict'
            }
        """
        func = self.get_plugin_method("init")
        response = func(params.dict())
        _LOGGER.debug(f"[WebhookService] init -> {response}")
        return WebhookResponse(**response)

    @transaction
    @convert_model
    def verify(self, params: WebhookVerityRequest) -> None:
        """verifying plugin

        :param params: WebhookRequest: {
                'options': 'dict'   # Request
            }

        :return:
            None
        """

        func = self.get_plugin_method("verify")
        func(params.dict())
