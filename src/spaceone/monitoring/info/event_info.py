import functools
from spaceone.api.monitoring.v1 import event_pb2
from spaceone.core.pygrpc.message_type import *
from spaceone.core import utils
from spaceone.monitoring.model.event_model import Event

__all__ = ['EventInfo', 'EventsInfo']


def EventResourceInfo(vo):
    if vo:
        info = {
            'resource_id': vo.resource_id,
            'resource_type': vo.resource_type,
            'name': vo.name
        }

        return event_pb2.EventResource(**info)
    else:
        return None


def EventInfo(event_vo: Event, minimal=False):
    info = {
        'event_id': event_vo.event_id,
        'event_key': event_vo.event_key,
        'event_type': event_vo.event_type,
        'title': event_vo.title,
        'severity': event_vo.severity,
        'alert_id': event_vo.alert_id
    }

    if not minimal:
        info.update({
            'description': event_vo.description,
            'rule': event_vo.rule,
            'image_url': event_vo.image_url,
            'resource': EventResourceInfo(event_vo.resource),
            'raw_data': change_struct_type(event_vo.raw_data),
            'additional_info': change_struct_type(event_vo.additional_info),
            'alert_id': event_vo.alert_id,
            'webhook_id': event_vo.webhook_id,
            'project_id': event_vo.project_id,
            'domain_id': event_vo.domain_id,
            'created_at': utils.datetime_to_iso8601(event_vo.created_at),
            'occurred_at': utils.datetime_to_iso8601(event_vo.occurred_at)
        })

    return event_pb2.EventInfo(**info)


def EventsInfo(note_vos, total_count, **kwargs):
    return event_pb2.EventsInfo(results=list(
        map(functools.partial(EventInfo, **kwargs), note_vos)), total_count=total_count)
