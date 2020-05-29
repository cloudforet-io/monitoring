from spaceone.api.monitoring.v1 import data_source_pb2, data_source_pb2_grpc
from spaceone.core.pygrpc import BaseAPI


class DataSource(BaseAPI, data_source_pb2_grpc.DataSourceServicer):

    pb2 = data_source_pb2
    pb2_grpc = data_source_pb2_grpc

    def register(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('DataSourceService', metadata) as data_source_service:
            return self.locator.get_info('DataSourceInfo', data_source_service.register(params))

    def update(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('DataSourceService', metadata) as data_source_service:
            return self.locator.get_info('DataSourceInfo', data_source_service.update(params))

    def enable(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('DataSourceService', metadata) as data_source_service:
            return self.locator.get_info('DataSourceInfo', data_source_service.enable(params))

    def disable(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('DataSourceService', metadata) as data_source_service:
            return self.locator.get_info('DataSourceInfo', data_source_service.disable(params))

    def deregister(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('DataSourceService', metadata) as data_source_service:
            data_source_service.deregister(params)
            return self.locator.get_info('EmptyInfo')

    def verify_plugin(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('DataSourceService', metadata) as data_source_service:
            return self.locator.get_info('VerifyInfo', data_source_service.verify_plugin(params))

    def get(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('DataSourceService', metadata) as data_source_service:
            return self.locator.get_info('DataSourceInfo', data_source_service.get(params))

    def list(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('DataSourceService', metadata) as data_source_service:
            data_source_vos, total_count = data_source_service.list(params)
            return self.locator.get_info('DataSourcesInfo',
                                         data_source_vos,
                                         total_count,
                                         minimal=self.get_minimal(params))

    def stat(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('DataSourceService', metadata) as data_source_service:
            return self.locator.get_info('StatisticsInfo', data_source_service.stat(params))
