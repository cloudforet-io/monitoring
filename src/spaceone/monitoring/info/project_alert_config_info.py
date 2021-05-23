import functools
from spaceone.api.monitoring.v1 import project_alert_config_pb2
from spaceone.core.pygrpc.message_type import *
from spaceone.core import utils
from spaceone.monitoring.model.project_alert_config_model import ProjectAlertConfig

__all__ = ['ProjectAlertConfigInfo', 'ProjectAlertConfigsInfo', 'VerifyInfo']


def ProjectAlertConfigInfo(project_alert_config_vo: ProjectAlertConfig, minimal=False):
    info = {
        'project_alert_config_id': project_alert_config_vo.project_alert_config_id,
        'name': project_alert_config_vo.name,
        'state': project_alert_config_vo.state,
        'monitoring_type': project_alert_config_vo.monitoring_type,
        'provider': project_alert_config_vo.provider
    }

    if not minimal:
        info.update({
            'capability': change_struct_type(project_alert_config_vo.capability),
            'plugin_info': PluginInfo(project_alert_config_vo.plugin_info),
            'tags': change_struct_type(utils.tags_to_dict(project_alert_config_vo.tags)),
            'domain_id': project_alert_config_vo.domain_id,
            'created_at': utils.datetime_to_iso8601(project_alert_config_vo.created_at)
        })

    return project_alert_config_pb2.ProjectAlertConfigInfo(**info)


def ProjectAlertConfigsInfo(project_alert_config_vos, total_count, **kwargs):
    return project_alert_config_pb2.ProjectAlertConfigsInfo(results=list(
        map(functools.partial(ProjectAlertConfigInfo, **kwargs), project_alert_config_vos)), total_count=total_count)


def VerifyInfo(is_verify):
    return project_alert_config_pb2.VerifyInfo(status=is_verify)
