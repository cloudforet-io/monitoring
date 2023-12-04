from spaceone.core.pygrpc import BaseAPI
from spaceone.api.monitoring.plugin import event_pb2, event_pb2_grpc
from spaceone.monitoring.plugin.webhook.service.event_service import EventService


class Event(BaseAPI, event_pb2_grpc.EventServicer):

    pb2 = event_pb2
    pb2_grpc = event_pb2_grpc

    def parse(self, request, context):
        params, metadata = self.parse_request(request, context)
        event_svc = EventService(metadata)
        for response in event_svc.get_data(params):
            yield self.dict_to_message(response)
