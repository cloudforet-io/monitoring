from spaceone.api.monitoring.v1 import webhook_pb2, webhook_pb2_grpc
from spaceone.core.pygrpc import BaseAPI


class Webhook(BaseAPI, webhook_pb2_grpc.WebhookServicer):

    pb2 = webhook_pb2
    pb2_grpc = webhook_pb2_grpc

    def create(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('WebhookService', metadata) as webhook_service:
            return self.locator.get_info('WebhookInfo', webhook_service.create(params))

    def update(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('WebhookService', metadata) as webhook_service:
            return self.locator.get_info('WebhookInfo', webhook_service.update(params))

    def enable(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('WebhookService', metadata) as webhook_service:
            return self.locator.get_info('WebhookInfo', webhook_service.enable(params))

    def disable(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('WebhookService', metadata) as webhook_service:
            return self.locator.get_info('WebhookInfo', webhook_service.disable(params))

    def delete(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('WebhookService', metadata) as webhook_service:
            webhook_service.delete(params)
            return self.locator.get_info('EmptyInfo')

    def update_plugin(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('WebhookService', metadata) as webhook_service:
            return self.locator.get_info('WebhookInfo', webhook_service.update_plugin(params))

    def verify_plugin(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('WebhookService', metadata) as webhook_service:
            webhook_service.verify_plugin(params)
            return self.locator.get_info('EmptyInfo')

    def get(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('WebhookService', metadata) as webhook_service:
            return self.locator.get_info('WebhookInfo', webhook_service.get(params))

    def list(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('WebhookService', metadata) as webhook_service:
            webhook_vos, total_count = webhook_service.list(params)
            return self.locator.get_info('WebhooksInfo',
                                         webhook_vos,
                                         total_count,
                                         minimal=self.get_minimal(params))

    def stat(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('WebhookService', metadata) as webhook_service:
            return self.locator.get_info('StatisticsInfo', webhook_service.stat(params))
