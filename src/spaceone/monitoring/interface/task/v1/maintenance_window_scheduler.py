import logging

from spaceone.core import config
from spaceone.core.token import get_token
from spaceone.core.locator import Locator
from spaceone.core.scheduler import IntervalScheduler

_LOGGER = logging.getLogger(__name__)


class MaintenanceWindowScheduler(IntervalScheduler):

    def __init__(self, queue, interval):
        super().__init__(queue, interval)
        self.locator = Locator()
        self._init_config()
        self._create_metadata()

    def _init_config(self):
        self._token = get_token('TOKEN')

    def _create_metadata(self):
        self._metadata = {
            'token': self._token,
            'service': 'monitoring',
            'resource': 'MaintenanceWindow',
            'verb': 'close_maintenance_window'
        }

    def create_task(self):
        stp = {
            'name': 'maintenance_window_schedule',
            'version': 'v1',
            'executionEngine': 'BaseWorker',
            'stages': [{
                'locator': 'SERVICE',
                'name': 'MaintenanceWindowService',
                'metadata': self._metadata,
                'method': 'close_maintenance_window',
                'params': {
                    'params': {}
                }
            }]
        }

        return [stp]
