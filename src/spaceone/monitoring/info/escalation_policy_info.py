import functools
from typing import List
from spaceone.api.monitoring.v1 import escalation_policy_pb2
from spaceone.core.pygrpc.message_type import *
from spaceone.core import utils

from spaceone.monitoring.model.escalation_policy_model import EscalationPolicy, EscalationRule

__all__ = ['EscalationPolicyInfo', 'EscalationPoliciesInfo']


def EscalationRulesInfo(vos: List[EscalationRule]):
    if vos:
        rules = []
        for vo in vos:
            info = {
                'notification_level': vo.notification_level,
                'escalate_minutes': vo.escalate_minutes
            }
            rule = escalation_policy_pb2.EscalationPolicyRule(**info)
            rules.append(rule)

        return rules
    else:
        return None


def EscalationPolicyInfo(escalation_policy_vo: EscalationPolicy, minimal=False):
    info = {
        'escalation_policy_id': escalation_policy_vo.escalation_policy_id,
        'name': escalation_policy_vo.name,
        'is_default': escalation_policy_vo.is_default
    }

    if not minimal:
        info.update({
            'rules': EscalationRulesInfo(escalation_policy_vo.rules),
            'repeat_count': escalation_policy_vo.repeat_count,
            'finish_condition': escalation_policy_vo.finish_condition,
            'tags': change_struct_type(escalation_policy_vo.tags),
            'scope': escalation_policy_vo.scope,
            'project_id': escalation_policy_vo.project_id,
            'domain_id': escalation_policy_vo.domain_id,
            'created_at': utils.datetime_to_iso8601(escalation_policy_vo.created_at)
        })

    return escalation_policy_pb2.EscalationPolicyInfo(**info)


def EscalationPoliciesInfo(escalation_policy_vos, total_count, **kwargs):
    return escalation_policy_pb2.EscalationPoliciesInfo(results=list(
        map(functools.partial(EscalationPolicyInfo, **kwargs), escalation_policy_vos)), total_count=total_count)
