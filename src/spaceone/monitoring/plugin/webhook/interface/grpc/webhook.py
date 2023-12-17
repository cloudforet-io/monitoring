from spaceone.core.pygrpc import BaseAPI
from spaceone.api.monitoring.plugin import webhook_pb2, webhook_pb2_grpc
from spaceone.monitoring.plugin.webhook.service.webhook_service import WebhookService


class Webhook(BaseAPI, webhook_pb2_grpc.WebhookServicer):
    pb2 = webhook_pb2
    pb2_grpc = webhook_pb2_grpc

    def init(self, request, context):
        params, metadata = self.parse_request(request, context)
        webhook_svc = WebhookService(metadata)
        response: dict = webhook_svc.init(params)
        return self.dict_to_message(response)

    def verify(self, request, context):
        params, metadata = self.parse_request(request, context)
        webhook_svc = WebhookService(metadata)
        webhook_svc.verify(params)
        return self.empty()
