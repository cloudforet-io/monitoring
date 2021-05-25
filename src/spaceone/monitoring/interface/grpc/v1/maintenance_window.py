from spaceone.api.monitoring.v1 import maintenance_window_pb2, maintenance_window_pb2_grpc
from spaceone.core.pygrpc import BaseAPI


class MaintenanceWindow(BaseAPI, maintenance_window_pb2_grpc.MaintenanceWindowServicer):

    pb2 = maintenance_window_pb2
    pb2_grpc = maintenance_window_pb2_grpc

    def create(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('MaintenanceWindowService', metadata) as maintenance_window_service:
            return self.locator.get_info('MaintenanceWindowInfo', maintenance_window_service.create(params))

    def update(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('MaintenanceWindowService', metadata) as maintenance_window_service:
            return self.locator.get_info('MaintenanceWindowInfo', maintenance_window_service.update(params))

    def close(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('MaintenanceWindowService', metadata) as maintenance_window_service:
            return self.locator.get_info('MaintenanceWindowInfo', maintenance_window_service.close(params))

    def get(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('MaintenanceWindowService', metadata) as maintenance_window_service:
            return self.locator.get_info('MaintenanceWindowInfo', maintenance_window_service.get(params))

    def list(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('MaintenanceWindowService', metadata) as maintenance_window_service:
            maintenance_window_vos, total_count = maintenance_window_service.list(params)
            return self.locator.get_info('MaintenanceWindowsInfo',
                                         maintenance_window_vos,
                                         total_count,
                                         minimal=self.get_minimal(params))

    def stat(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('MaintenanceWindowService', metadata) as maintenance_window_service:
            return self.locator.get_info('StatisticsInfo', maintenance_window_service.stat(params))
