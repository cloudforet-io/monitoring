import functools
from typing import List
from spaceone.api.monitoring.v1 import alert_pb2
from spaceone.core.pygrpc.message_type import *
from spaceone.core import utils

from spaceone.monitoring.model.alert_model import Alert, Responder

__all__ = ['AlertInfo', 'AlertsInfo']


def RespondersInfo(vos: List[Responder]):
    if vos:
        responders = []
        for vo in vos:
            info = {
                'resource_type': vo.resource_type,
                'resource_id': vo.resource_id
            }
            responder = alert_pb2.AlertResponder(**info)
            responders.append(responder)

        return responders
    else:
        return None


def AlertResourceInfo(vo):
    if vo:
        info = {
            'resource_id': vo.resource_id,
            'resource_type': vo.resource_type,
            'name': vo.name
        }

        return alert_pb2.AlertResource(**info)
    else:
        return None


def AlertInfo(alert_vo: Alert, minimal=False):
    info = {
        'alert_number': alert_vo.alert_number,
        'alert_id': alert_vo.alert_id,
        'title': alert_vo.title,
        'state': alert_vo.state,
        'status_message': alert_vo.status_message,
        'assignee': alert_vo.assignee,
        'urgency': alert_vo.urgency,
        'escalation_step': alert_vo.escalation_step,
        'escalation_ttl': alert_vo.escalation_ttl,
        'project_id': alert_vo.project_id
    }

    if not minimal:
        info.update({
            'description': alert_vo.description,
            'severity': alert_vo.severity,
            'rule': alert_vo.rule,
            'image_url': alert_vo.image_url,
            'resource': AlertResourceInfo(alert_vo.resource),
            'additional_info': change_struct_type(alert_vo.additional_info),
            'is_snoozed': alert_vo.is_snoozed,
            'snoozed_end_time': utils.datetime_to_iso8601(alert_vo.snoozed_end_time),
            'responders': RespondersInfo(alert_vo.responders),
            'project_dependencies': alert_vo.project_dependencies,
            'triggered_by': alert_vo.triggered_by,
            'webhook_id': alert_vo.webhook_id,
            'escalation_policy_id': alert_vo.escalation_policy_id,
            'domain_id': alert_vo.domain_id,
            'created_at': utils.datetime_to_iso8601(alert_vo.created_at),
            'updated_at': utils.datetime_to_iso8601(alert_vo.updated_at),
            'acknowledged_at': utils.datetime_to_iso8601(alert_vo.acknowledged_at),
            'resolved_at': utils.datetime_to_iso8601(alert_vo.resolved_at),
            'escalated_at': utils.datetime_to_iso8601(alert_vo.escalated_at)
        })

    return alert_pb2.AlertInfo(**info)


def AlertsInfo(alert_vos, total_count, **kwargs):
    return alert_pb2.AlertsInfo(results=list(
        map(functools.partial(AlertInfo, **kwargs), alert_vos)), total_count=total_count)
