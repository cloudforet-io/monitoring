import functools
from spaceone.api.monitoring.v1 import project_alert_config_pb2
from spaceone.core import utils
from spaceone.monitoring.model.project_alert_config_model import ProjectAlertConfig, NotificationOptions

__all__ = ['ProjectAlertConfigInfo', 'ProjectAlertConfigsInfo']


def NotificationOptionsInfo(vo: NotificationOptions):
    if vo:
        info = {
            'urgency': vo.urgency
        }

        return project_alert_config_pb2.NotificationOptions(**info)
    else:
        return None


def ProjectAlertConfigInfo(project_alert_config_vo: ProjectAlertConfig, minimal=False):
    info = {
        'project_id': project_alert_config_vo.project_id,
        'notification_options': NotificationOptionsInfo(project_alert_config_vo.notification_options)
    }

    if not minimal:
        info.update({
            'domain_id': project_alert_config_vo.domain_id,
            'created_at': utils.datetime_to_iso8601(project_alert_config_vo.created_at)
        })

    return project_alert_config_pb2.ProjectAlertConfigInfo(**info)


def ProjectAlertConfigsInfo(project_alert_config_vos, total_count, **kwargs):
    return project_alert_config_pb2.ProjectAlertConfigsInfo(results=list(
        map(functools.partial(ProjectAlertConfigInfo, **kwargs), project_alert_config_vos)), total_count=total_count)
