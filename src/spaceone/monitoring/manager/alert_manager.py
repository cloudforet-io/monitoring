import logging

from spaceone.core.manager import BaseManager
from spaceone.monitoring.model.alert_model import Alert
from spaceone.monitoring.error.alert import *

_LOGGER = logging.getLogger(__name__)


class AlertManager(BaseManager):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.alert_model: Alert = self.locator.get_model('Alert')

    def create_alert(self, params):
        def _rollback(alert_vo):
            _LOGGER.info(f'[create_alert._rollback] '
                         f'Delete alert : #{str(alert_vo.alert_number)} '
                         f'({alert_vo.alert_id})')
            alert_vo.delete()

        alert_vo: Alert = self.alert_model.create(params)
        self.transaction.add_rollback(_rollback, alert_vo)

        return alert_vo

    def update_alert(self, params):
        alert_vo: Alert = self.get_alert(params['alert_id'], params['domain_id'])
        return self.update_alert_by_vo(params, alert_vo)

    def update_alert_by_vo(self, params, alert_vo):
        def _rollback(old_data):
            _LOGGER.info(f'[update_alert_by_vo._rollback] Revert Data : '
                         f'{old_data["alert_id"]}')
            alert_vo.update(old_data)

        self.transaction.add_rollback(_rollback, alert_vo.to_dict())
        return alert_vo.update(params)

    def add_responder(self, params):
        resource_type = params['resource_type']
        resource_id = params['resource_id']

        alert_vo: Alert = self.get_alert(params['alert_id'], params['domain_id'])

        for responder in alert_vo.responders:
            if responder.resource_type == resource_type and responder.resource_id == resource_id:
                raise ERROR_SAME_RESPONDER_ALREADY_EXISTS(resource_type=resource_type, resource_id=resource_id)

        alert_vo = alert_vo.append('responders', {'resource_type': resource_type, 'resource_id': resource_id})
        return alert_vo

    def remove_responder(self, params):
        resource_type = params['resource_type']
        resource_id = params['resource_id']

        alert_vo: Alert = self.get_alert(params['alert_id'], params['domain_id'])

        for responder in alert_vo.responders:
            if responder.resource_type == resource_type and responder.resource_id == resource_id:
                alert_vo = alert_vo.remove('responders', {'resource_type': resource_type, 'resource_id': resource_id})
                return alert_vo

        raise ERROR_RESPONDER_NOT_EXIST(resource_type=resource_type, resource_id=resource_id)

    def add_project_dependency(self, params):
        project_id = params['project_id']

        alert_vo: Alert = self.get_alert(params['alert_id'], params['domain_id'])

        for project_dependency in alert_vo.project_dependencies:
            if project_dependency == project_id:
                raise ERROR_SAME_PROJECT_DEPENDENCY_ALREADY_EXISTS(project_id=project_id)

        alert_vo = alert_vo.append('project_dependencies', project_id)
        return alert_vo

    def remove_project_dependency(self, params):
        project_id = params['project_id']

        alert_vo: Alert = self.get_alert(params['alert_id'], params['domain_id'])

        for project_dependency in alert_vo.project_dependencies:
            if project_dependency == project_id:
                alert_vo = alert_vo.remove('project_dependencies', project_id)
                return alert_vo

        raise ERROR_PROJECT_DEPENDENCY_NOT_EXIST(project_id=project_id)

    def delete_alert(self, alert_id, domain_id):
        alert_vo: Alert = self.get_alert(alert_id, domain_id)
        alert_vo.delete()

    def get_alert(self, alert_id, domain_id, only=None):
        return self.alert_model.get(alert_id=alert_id, domain_id=domain_id, only=only)

    def list_alerts(self, query={}):
        return self.alert_model.query(**query)

    def stat_alerts(self, query):
        return self.alert_model.stat(**query)
