import logging
from datetime import datetime
from typing import Union

from spaceone.core.error import *
from spaceone.core import queue, utils
from spaceone.core.manager import BaseManager
from spaceone.monitoring.model.job_model import Job
from spaceone.monitoring.model.alert_model import Alert

_LOGGER = logging.getLogger(__name__)


class JobManager(BaseManager):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.job_model: Job = self.locator.get_model('Job')
        self.job_vo: Union[Job, None] = None

    def is_domain_job_running(self, domain_id):
        job_vos = self.job_model.filter(domain_id=domain_id, status='IN_PROGRESS')

        if job_vos.count() == 0:
            return False

        for job_vo in job_vos:
            # Old jobs change to timeout status
            pass

        return True

    def create_job(self, domain_id):
        self.job_vo = self.job_model.create({'domain_id': domain_id})

    def start_job(self):
        try:
            _LOGGER.debug(f'[start_job] Start Job: {self.job_vo.domain_id} ({self.job_vo.job_id})')
            self.job_vo.delete()
        except ERROR_BASE as e:
            self._change_error_status(e)
        except Exception as e:
            self._change_error_status(ERROR_UNKNOWN(message=str(e)))

    def _change_error_status(self, e):
        _LOGGER.error(f'Job Error: {e.message}')
        self.job_vo.update({
            'status': 'ERROR',
            'error': {
                'error_code': e.error_code,
                'message': e.message
            },
            'finished_at': datetime.utcnow()
        })

    def push_task(self, task_name, class_name, method, params):
        task = {
            'name': task_name,
            'version': 'v1',
            'executionEngine': 'BaseWorker',
            'stages': [{
                'locator': 'SERVICE',
                'name': class_name,
                'metadata': self.transaction.meta,
                'method': method,
                'params': {
                    'params': params
                }
            }]
        }

        queue.put('monitoring_q', utils.dump_json(task))
