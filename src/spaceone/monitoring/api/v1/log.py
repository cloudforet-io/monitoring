from spaceone.api.monitoring.v1 import log_pb2, log_pb2_grpc
from spaceone.core.pygrpc import BaseAPI


class Log(BaseAPI, log_pb2_grpc.LogServicer):

    pb2 = log_pb2
    pb2_grpc = log_pb2_grpc

    def list(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('LogService', metadata) as log_service:
            return self.locator.get_info('LogDataInfo', log_service.list(params))
