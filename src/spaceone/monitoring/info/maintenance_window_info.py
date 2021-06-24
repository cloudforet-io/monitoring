import functools
from spaceone.api.monitoring.v1 import maintenance_window_pb2
from spaceone.core.pygrpc.message_type import *
from spaceone.core import utils
from spaceone.monitoring.model.maintenance_window_model import MaintenanceWindow

__all__ = ['MaintenanceWindowInfo', 'MaintenanceWindowsInfo']


def MaintenanceWindowInfo(maintenance_window_vo: MaintenanceWindow, minimal=False):
    info = {
        'maintenance_window_id': maintenance_window_vo.maintenance_window_id,
        'title': maintenance_window_vo.title,
        'state': maintenance_window_vo.state,
        'projects': maintenance_window_vo.projects,
        'start_time': utils.datetime_to_iso8601(maintenance_window_vo.start_time),
        'end_time': utils.datetime_to_iso8601(maintenance_window_vo.end_time)
    }

    if not minimal:
        info.update({
            'tags': change_struct_type(maintenance_window_vo.tags),
            'domain_id': maintenance_window_vo.domain_id,
            'created_by': maintenance_window_vo.created_by,
            'created_at': utils.datetime_to_iso8601(maintenance_window_vo.created_at),
            'updated_at': utils.datetime_to_iso8601(maintenance_window_vo.updated_at),
            'closed_at': utils.datetime_to_iso8601(maintenance_window_vo.closed_at)
        })

    return maintenance_window_pb2.MaintenanceWindowInfo(**info)


def MaintenanceWindowsInfo(maintenance_window_vos, total_count, **kwargs):
    return maintenance_window_pb2.MaintenanceWindowsInfo(results=list(
        map(functools.partial(MaintenanceWindowInfo, **kwargs), maintenance_window_vos)), total_count=total_count)
