from spaceone.api.monitoring.v1 import alert_pb2, alert_pb2_grpc
from spaceone.core.pygrpc import BaseAPI


class Alert(BaseAPI, alert_pb2_grpc.AlertServicer):

    pb2 = alert_pb2
    pb2_grpc = alert_pb2_grpc

    def create(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('AlertService', metadata) as alert_service:
            return self.locator.get_info('AlertInfo', alert_service.create(params))

    def update(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('AlertService', metadata) as alert_service:
            return self.locator.get_info('AlertInfo', alert_service.update(params))

    def update_state(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('AlertService', metadata) as alert_service:
            return self.locator.get_info('AlertInfo', alert_service.update_state(params))

    def merge(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('AlertService', metadata) as alert_service:
            return self.locator.get_info('AlertInfo', alert_service.merge(params))

    def snooze(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('AlertService', metadata) as alert_service:
            return self.locator.get_info('AlertInfo', alert_service.snooze(params))

    def add_responder(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('AlertService', metadata) as alert_service:
            return self.locator.get_info('AlertInfo', alert_service.add_responder(params))

    def remove_responder(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('AlertService', metadata) as alert_service:
            return self.locator.get_info('AlertInfo', alert_service.remove_responder(params))

    def add_project_dependency(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('AlertService', metadata) as alert_service:
            return self.locator.get_info('AlertInfo', alert_service.add_project_dependency(params))

    def remove_project_dependency(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('AlertService', metadata) as alert_service:
            return self.locator.get_info('AlertInfo', alert_service.remove_project_dependency(params))

    def delete(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('AlertService', metadata) as alert_service:
            alert_service.delete(params)
            return self.locator.get_info('EmptyInfo')

    def get(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('AlertService', metadata) as alert_service:
            return self.locator.get_info('AlertInfo', alert_service.get(params))

    def list(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('AlertService', metadata) as alert_service:
            alert_vos, total_count = alert_service.list(params)
            return self.locator.get_info('AlertsInfo',
                                         alert_vos,
                                         total_count,
                                         minimal=self.get_minimal(params))

    def stat(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('AlertService', metadata) as alert_service:
            return self.locator.get_info('StatisticsInfo', alert_service.stat(params))
