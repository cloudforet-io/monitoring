from spaceone.api.monitoring.v1 import event_rule_pb2, event_rule_pb2_grpc
from spaceone.core.pygrpc import BaseAPI


class EventRule(BaseAPI, event_rule_pb2_grpc.EventRuleServicer):

    pb2 = event_rule_pb2
    pb2_grpc = event_rule_pb2_grpc

    def create(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('EventRuleService', metadata) as event_rule_service:
            return self.locator.get_info('EventRuleInfo', event_rule_service.create(params))

    def update(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('EventRuleService', metadata) as event_rule_service:
            return self.locator.get_info('EventRuleInfo', event_rule_service.update(params))

    def change_order(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('EventRuleService', metadata) as event_rule_service:
            return self.locator.get_info('EventRuleInfo', event_rule_service.change_order(params))

    def delete(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('EventRuleService', metadata) as event_rule_service:
            event_rule_service.delete(params)
            return self.locator.get_info('EmptyInfo')

    def get(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('EventRuleService', metadata) as event_rule_service:
            return self.locator.get_info('EventRuleInfo', event_rule_service.get(params))

    def list(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('EventRuleService', metadata) as event_rule_service:
            event_rule_vos, total_count = event_rule_service.list(params)
            return self.locator.get_info('EventRulesInfo',
                                         event_rule_vos,
                                         total_count,
                                         minimal=self.get_minimal(params))

    def stat(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('EventRuleService', metadata) as event_rule_service:
            return self.locator.get_info('StatisticsInfo', event_rule_service.stat(params))
