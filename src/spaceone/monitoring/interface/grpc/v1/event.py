from spaceone.api.monitoring.v1 import event_pb2, event_pb2_grpc
from spaceone.core.pygrpc import BaseAPI


class Event(BaseAPI, event_pb2_grpc.EventServicer):

    pb2 = event_pb2
    pb2_grpc = event_pb2_grpc

    def create(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('EventService', metadata) as event_service:
            event_service.create(params)
            return self.locator.get_info('EmptyInfo')

    def get(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('EventService', metadata) as event_service:
            return self.locator.get_info('EventInfo', event_service.get(params))

    def list(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('EventService', metadata) as event_service:
            event_vos, total_count = event_service.list(params)
            return self.locator.get_info('EventsInfo',
                                         event_vos,
                                         total_count,
                                         minimal=self.get_minimal(params))

    def stat(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('EventService', metadata) as event_service:
            return self.locator.get_info('StatisticsInfo', event_service.stat(params))
