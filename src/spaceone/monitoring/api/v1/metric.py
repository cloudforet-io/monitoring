from spaceone.api.monitoring.v1 import metric_pb2, metric_pb2_grpc
from spaceone.core.pygrpc import BaseAPI


class Metric(BaseAPI, metric_pb2_grpc.MetricServicer):

    pb2 = metric_pb2
    pb2_grpc = metric_pb2_grpc

    def list(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('MetricService', metadata) as metric_service:
            return self.locator.get_info('MetricsInfo', metric_service.list(params))

    def get_data(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('MetricService', metadata) as metric_service:
            return self.locator.get_info('MetricDataInfo', metric_service.get_data(params))
