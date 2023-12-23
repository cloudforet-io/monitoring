import functools
from typing import List

from spaceone.api.monitoring.v1 import event_rule_pb2
from spaceone.core import utils
from spaceone.core.pygrpc.message_type import *

from spaceone.monitoring.model.event_rule_model import (
    EventRule,
    EventRuleCondition,
    EventRuleOptions,
)

__all__ = ["EventRuleInfo", "EventRulesInfo"]


def EventRuleConditionsInfo(condition_vos: List[EventRuleCondition]):
    if condition_vos is None:
        condition_vos = []

    conditions_info = []

    for vo in condition_vos:
        info = {"key": vo.key, "value": vo.value, "operator": vo.operator}

        conditions_info.append(event_rule_pb2.EventRuleCondition(**info))

    return conditions_info


def EventRuleActionsInfo(actions_data):
    if actions_data is None:
        return None
    else:
        info = {}

        for key, value in actions_data.items():
            if key == "add_additional_info":
                info[key] = change_struct_type(value)
            else:
                info[key] = value

        return event_rule_pb2.EventRuleActions(**info)


def EventRuleOptionsInfo(vo: EventRuleOptions):
    if vo is None:
        return None
    else:
        info = {"stop_processing": vo.stop_processing}

        return event_rule_pb2.EventRuleOptions(**info)


def EventRuleInfo(event_rule_vo: EventRule, minimal=False):
    info = {
        "event_rule_id": event_rule_vo.event_rule_id,
        "name": event_rule_vo.name,
        "order": event_rule_vo.order,
        "resource_group": event_rule_vo.resource_group,
        "project_id": event_rule_vo.project_id,
    }

    if not minimal:
        info.update(
            {
                "conditions": EventRuleConditionsInfo(event_rule_vo.conditions),
                "conditions_policy": event_rule_vo.conditions_policy,
                "actions": EventRuleActionsInfo(event_rule_vo.actions),
                "options": EventRuleOptionsInfo(event_rule_vo.options),
                "tags": change_struct_type(event_rule_vo.tags),
                "workspace_id": event_rule_vo.workspace_id,
                "domain_id": event_rule_vo.domain_id,
                "created_at": utils.datetime_to_iso8601(event_rule_vo.created_at),
            }
        )

    return event_rule_pb2.EventRuleInfo(**info)


def EventRulesInfo(event_rule_vos, total_count, **kwargs):
    return event_rule_pb2.EventRulesInfo(
        results=list(map(functools.partial(EventRuleInfo, **kwargs), event_rule_vos)),
        total_count=total_count,
    )
