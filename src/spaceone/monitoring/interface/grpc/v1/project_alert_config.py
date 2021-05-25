from spaceone.api.monitoring.v1 import project_alert_config_pb2, project_alert_config_pb2_grpc
from spaceone.core.pygrpc import BaseAPI


class ProjectAlertConfig(BaseAPI, project_alert_config_pb2_grpc.ProjectAlertConfigServicer):

    pb2 = project_alert_config_pb2
    pb2_grpc = project_alert_config_pb2_grpc

    def create(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('ProjectAlertConfigService', metadata) as project_alert_config_service:
            return self.locator.get_info('ProjectAlertConfigInfo', project_alert_config_service.create(params))

    def update(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('ProjectAlertConfigService', metadata) as project_alert_config_service:
            return self.locator.get_info('ProjectAlertConfigInfo', project_alert_config_service.update(params))

    def delete(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('ProjectAlertConfigService', metadata) as project_alert_config_service:
            project_alert_config_service.delete(params)
            return self.locator.get_info('EmptyInfo')

    def get(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('ProjectAlertConfigService', metadata) as project_alert_config_service:
            return self.locator.get_info('ProjectAlertConfigInfo', project_alert_config_service.get(params))

    def list(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('ProjectAlertConfigService', metadata) as project_alert_config_service:
            project_alert_config_vos, total_count = project_alert_config_service.list(params)
            return self.locator.get_info('ProjectAlertConfigsInfo',
                                         project_alert_config_vos,
                                         total_count,
                                         minimal=self.get_minimal(params))

    def stat(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('ProjectAlertConfigService', metadata) as project_alert_config_service:
            return self.locator.get_info('StatisticsInfo', project_alert_config_service.stat(params))
