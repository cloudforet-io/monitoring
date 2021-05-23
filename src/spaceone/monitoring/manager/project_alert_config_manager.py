import logging

from spaceone.core.manager import BaseManager
from spaceone.monitoring.model.project_alert_config_model import ProjectAlertConfig

_LOGGER = logging.getLogger(__name__)


class ProjectAlertConfigManager(BaseManager):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.project_alert_config_model: ProjectAlertConfig = self.locator.get_model('ProjectAlertConfig')

    def create_project_alert_config(self, params):
        def _rollback(project_alert_config_vo: ProjectAlertConfig):
            _LOGGER.info(f'[create_project_alert_config._rollback] '
                         f'Delete project alert config : {project_alert_config_vo.project_id}')
            project_alert_config_vo.delete()

        project_alert_config_vo: ProjectAlertConfig = self.project_alert_config_model.create(params)
        self.transaction.add_rollback(_rollback, project_alert_config_vo)

        return project_alert_config_vo

    def update_project_alert_config(self, params):
        project_alert_config_vo: ProjectAlertConfig = self.get_project_alert_config(params['project_id'],
                                                                                    params['domain_id'])
        return self.update_project_alert_config_by_vo(params, project_alert_config_vo)

    def update_project_alert_config_by_vo(self, params, project_alert_config_vo):
        def _rollback(old_data):
            _LOGGER.info(f'[update_project_alert_config_by_vo._rollback] Revert Data : '
                         f'{old_data["project_id"]}')
            project_alert_config_vo.update(old_data)

        self.transaction.add_rollback(_rollback, project_alert_config_vo.to_dict())

        return project_alert_config_vo.update(params)

    def delete_project_alert_config(self, project_id, domain_id):
        project_alert_config_vo: ProjectAlertConfig = self.get_project_alert_config(project_id, domain_id)
        project_alert_config_vo.delete()

    def get_project_alert_config(self, project_id, domain_id, only=None):
        return self.project_alert_config_model.get(project_id=project_id, domain_id=domain_id, only=only)

    def list_project_alert_configs(self, query={}):
        return self.project_alert_config_model.query(**query)

    def stat_project_alert_configs(self, query):
        return self.project_alert_config_model.stat(**query)
