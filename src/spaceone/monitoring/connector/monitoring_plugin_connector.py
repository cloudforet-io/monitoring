import logging

from google.protobuf.json_format import MessageToDict

from spaceone.core.connector import BaseConnector
from spaceone.core import pygrpc
from spaceone.core.utils import parse_endpoint
from spaceone.core.error import *

__all__ = ['MonitoringPluginConnector']

_LOGGER = logging.getLogger(__name__)


class MonitoringPluginConnector(BaseConnector):

    def __init__(self, transaction, config):
        super().__init__(transaction, config)

    def initialize(self, endpoint):
        e = parse_endpoint(endpoint)
        self.client = pygrpc.client(endpoint=f'{e.get("hostname")}:{e.get("port")}', version='plugin')

    def verify(self, options, secret_data):
        response = self.client.DataSource.verify({
            'options': options,
            'secret_data': secret_data
        }, metadata=self.transaction.get_connection_meta())

        return self._change_message(response)

    def list_metrics(self, options, secret_data, resource):
        responses = self.client.Metric.list({
            'options': options,
            'secret_data': secret_data,
            'resource': resource
        }, metadata=self.transaction.get_connection_meta())

        return self._change_message(responses)

    def get_metric_data(self, options, secret_data, resource, metric, start, end, period, stat):
        responses = self.client.Metric.get_data({
            'options': options,
            'secret_data': secret_data,
            'resource': resource,
            'metric': metric,
            'start': start,
            'end': end,
            'period': period,
            'stat': stat
        }, metadata=self.transaction.get_connection_meta())

        return self._change_message(responses)

    def list_logs(self, options, secret_data, resource, plugin_filter, start, end, sort, limit):
        responses = self.client.Log.list({
            'options': options,
            'secret_data': secret_data,
            'resource': resource,
            'filter': plugin_filter,
            'start': start,
            'end': end,
            'sort': sort,
            'limit': limit
        }, metadata=self.transaction.get_connection_meta())

        return self._change_message(responses)

    @staticmethod
    def _change_message(messages):
        for message in messages:
            yield MessageToDict(message, preserving_proto_field_name=True)
