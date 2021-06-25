import logging
from typing import List
from datetime import datetime, timedelta

from spaceone.core.error import *
from spaceone.core import queue, utils, config
from spaceone.core.manager import BaseManager
from spaceone.monitoring.model.job_model import Job

_LOGGER = logging.getLogger(__name__)


class JobManager(BaseManager):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.job_model: Job = self.locator.get_model('Job')
        self.job_timeout = config.get_global('JOB_TIMEOUT', 600)

    def is_domain_job_running(self, domain_id):
        job_vos: List[Job] = self.job_model.filter(domain_id=domain_id, status='IN_PROGRESS')

        running_job_count = job_vos.count()

        for job_vo in job_vos:
            if job_vo.remained_tasks == 0 and job_vo.status not in ['ERROR', 'TIMEOUT']:
                self.change_success_status(job_vo)
                running_job_count -= 1

            if datetime.utcnow() > (job_vo.created_at + timedelta(seconds=self.job_timeout)):
                self.change_timeout_status(job_vo)
                running_job_count -= 1

        if running_job_count > 0:
            return True
        else:
            return False

    def create_job(self, domain_id):
        return self.job_model.create({'domain_id': domain_id})

    def get_job(self, job_id, domain_id):
        return self.job_model.get(job_id=job_id, domain_id=domain_id)

    @staticmethod
    def decrease_remained_tasks(job_vo: Job):
        job_vo.decrement('remained_tasks', 1)

    @staticmethod
    def change_success_status(job_vo: Job):
        job_vo.delete()
        # job_vo.update({
        #     'status': 'SUCCESS',
        #     'finished_at': datetime.utcnow()
        # })

    @staticmethod
    def change_timeout_status(job_vo: Job):
        _LOGGER.error(f'Job Timeout ({job_vo.job_id}): {job_vo.domain_id}')

        job_vo.update({
            'status': 'TIMEOUT',
            'finished_at': datetime.utcnow()
        })

    @staticmethod
    def change_error_status(job_vo: Job, e):
        if not isinstance(e, ERROR_BASE):
            e = ERROR_UNKNOWN(message=str(e))

        _LOGGER.error(f'Job Error ({job_vo.job_id}): {e.message}', exc_info=True)

        job_vo.update({
            'status': 'ERROR',
            'finished_at': datetime.utcnow()
        })

        job_vo.append('errors', {
            'error_code': e.error_code,
            'message': e.message
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
