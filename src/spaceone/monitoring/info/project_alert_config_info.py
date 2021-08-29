import functools
from spaceone.api.monitoring.v1 import project_alert_config_pb2
from spaceone.core import utils
from spaceone.monitoring.model.project_alert_config_model import ProjectAlertConfig, AlertOptions
from spaceone.monitoring.info.escalation_policy_info import EscalationPolicyInfo

__all__ = ['ProjectAlertConfigInfo', 'ProjectAlertConfigsInfo']


def AlertOptionsInfo(vo: AlertOptions):
    if vo:
        info = {
            'notification_urgency': vo.notification_urgency,
            'recovery_mode': vo.recovery_mode,
        }

        return project_alert_config_pb2.AlertOptions(**info)
    else:
        return None


def ProjectAlertConfigInfo(project_alert_config_vo: ProjectAlertConfig, minimal=False):
    info = {
        'project_id': project_alert_config_vo.project_id,
        'options': AlertOptionsInfo(project_alert_config_vo.options)
    }

    if not minimal:
        info.update({
            'domain_id': project_alert_config_vo.domain_id,
            'created_at': utils.datetime_to_iso8601(project_alert_config_vo.created_at)
        })

        if project_alert_config_vo.escalation_policy:
            info['escalation_policy_info'] = EscalationPolicyInfo(project_alert_config_vo.escalation_policy,
                                                                  minimal=True)

    return project_alert_config_pb2.ProjectAlertConfigInfo(**info)


def ProjectAlertConfigsInfo(project_alert_config_vos, total_count, **kwargs):
    return project_alert_config_pb2.ProjectAlertConfigsInfo(results=list(
        map(functools.partial(ProjectAlertConfigInfo, **kwargs), project_alert_config_vos)), total_count=total_count)
