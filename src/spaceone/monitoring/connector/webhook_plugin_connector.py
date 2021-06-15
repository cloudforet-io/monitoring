import logging

from google.protobuf.json_format import MessageToDict

from spaceone.core.connector import BaseConnector
from spaceone.core import pygrpc
from spaceone.core.utils import parse_endpoint
from spaceone.core.error import *

__all__ = ['WebhookPluginConnector']

_LOGGER = logging.getLogger(__name__)


class WebhookPluginConnector(BaseConnector):

    def __init__(self, transaction, config):
        super().__init__(transaction, config)
        self.client = None

    def initialize(self, endpoint):
        static_endpoint = self.config.get('endpoint')

        if static_endpoint:
            endpoint = static_endpoint

        e = parse_endpoint(endpoint)
        self.client = pygrpc.client(endpoint=f'{e.get("hostname")}:{e.get("port")}', version='plugin')

    def init(self, options):
        response = self.client.Webhook.init({
            'options': options,
        }, metadata=self.transaction.get_connection_meta())

        return self._change_message(response)

    def verify(self, options):
        params = {
            'options': options
        }

        self.client.Webhook.verify(params, metadata=self.transaction.get_connection_meta())

    def parse_event(self, options, data):
        params = {
            'options': options,
            'data': data
        }

        response = self.client.Event.parse(params, metadata=self.transaction.get_connection_meta())
        return self._change_message(response)

    @staticmethod
    def _change_message(message):
        return MessageToDict(message, preserving_proto_field_name=True)
