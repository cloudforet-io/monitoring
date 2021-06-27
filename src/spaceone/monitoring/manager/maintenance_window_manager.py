import logging

from spaceone.core.manager import BaseManager
from spaceone.monitoring.model.maintenance_window_model import MaintenanceWindow

_LOGGER = logging.getLogger(__name__)


class MaintenanceWindowManager(BaseManager):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.maintenance_window_model: MaintenanceWindow = self.locator.get_model('MaintenanceWindow')

    def create_maintenance_window(self, params):
        def _rollback(maintenance_window_vo):
            _LOGGER.info(f'[create_maintenance_window._rollback] '
                         f'Delete maintenance_window : {maintenance_window_vo.title} '
                         f'({maintenance_window_vo.maintenance_window_id})')
            maintenance_window_vo.delete()

        maintenance_window_vo: MaintenanceWindow = self.maintenance_window_model.create(params)
        self.transaction.add_rollback(_rollback, maintenance_window_vo)

        return maintenance_window_vo

    def update_maintenance_window(self, params):
        maintenance_window_vo: MaintenanceWindow = self.get_maintenance_window(params['maintenance_window_id'],
                                                                               params['domain_id'])
        return self.update_maintenance_window_by_vo(params, maintenance_window_vo)

    def update_maintenance_window_by_vo(self, params, maintenance_window_vo):
        def _rollback(old_data):
            _LOGGER.info(f'[update_maintenance_window_by_vo._rollback] Revert Data : '
                         f'{old_data["maintenance_window_id"]}')
            maintenance_window_vo.update(old_data)

        self.transaction.add_rollback(_rollback, maintenance_window_vo.to_dict())

        return maintenance_window_vo.update(params)

    def close_maintenance_window(self, maintenance_window_id, domain_id):
        maintenance_window_vo: MaintenanceWindow = self.get_maintenance_window(maintenance_window_id, domain_id)

        return self.update_maintenance_window_by_vo({'state': 'CLOSED'}, maintenance_window_vo)

    def get_maintenance_window(self, maintenance_window_id, domain_id, only=None):
        return self.maintenance_window_model.get(maintenance_window_id=maintenance_window_id,
                                                 domain_id=domain_id, only=only)

    def list_open_maintenance_windows(self):
        return self.maintenance_window_model.filter(state='OPEN')

    def list_maintenance_windows(self, query={}):
        return self.maintenance_window_model.query(**query)

    def stat_maintenance_windows(self, query):
        return self.maintenance_window_model.stat(**query)
