from spaceone.api.monitoring.v1 import escalation_policy_pb2, escalation_policy_pb2_grpc
from spaceone.core.pygrpc import BaseAPI


class EscalationPolicy(BaseAPI, escalation_policy_pb2_grpc.EscalationPolicyServicer):

    pb2 = escalation_policy_pb2
    pb2_grpc = escalation_policy_pb2_grpc

    def create(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('EscalationPolicyService', metadata) as escalation_policy_service:
            return self.locator.get_info('EscalationPolicyInfo', escalation_policy_service.create(params))

    def update(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('EscalationPolicyService', metadata) as escalation_policy_service:
            return self.locator.get_info('EscalationPolicyInfo', escalation_policy_service.update(params))

    def set_default(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('EscalationPolicyService', metadata) as escalation_policy_service:
            return self.locator.get_info('EscalationPolicyInfo', escalation_policy_service.set_default(params))

    def delete(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('EscalationPolicyService', metadata) as escalation_policy_service:
            escalation_policy_service.delete(params)
            return self.locator.get_info('EmptyInfo')

    def get(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('EscalationPolicyService', metadata) as escalation_policy_service:
            return self.locator.get_info('EscalationPolicyInfo', escalation_policy_service.get(params))

    def list(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('EscalationPolicyService', metadata) as escalation_policy_service:
            escalation_policy_vos, total_count = escalation_policy_service.list(params)
            return self.locator.get_info('EscalationPoliciesInfo',
                                         escalation_policy_vos,
                                         total_count,
                                         minimal=self.get_minimal(params))

    def stat(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('EscalationPolicyService', metadata) as escalation_policy_service:
            return self.locator.get_info('StatisticsInfo', escalation_policy_service.stat(params))
