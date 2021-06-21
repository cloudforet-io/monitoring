import logging

from spaceone.core.service import *
from spaceone.monitoring.manager.alert_manager import AlertManager
from spaceone.monitoring.manager.job_manager import JobManager

_LOGGER = logging.getLogger(__name__)


@authentication_handler
@authorization_handler
@mutation_handler
@event_handler
class JobService(BaseService):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.job_mgr: JobManager = self.locator.get_manager('JobManager')

    @transaction(append_meta={'authorization.scope': 'SYSTEM'})
    @check_required(['domain_id'])
    def create(self, params):
        """ Create jobs by domain

        Args:
            params (dict): {
                'domain_id': 'str'
            }

        Returns:
            None
        """

        domain_id = params['domain_id']

        if self.job_mgr.is_domain_job_running(domain_id):
            return None

        self.job_mgr.create_job(domain_id)
        self.job_mgr.start_job()

    @transaction(append_meta={'authorization.scope': 'SYSTEM'})
    def create_jobs_by_domain(self, params):
        """ Create jobs by domain

        Args:
            params (dict): {}

        Returns:
            None
        """

        for domain_id in self._list_domains_of_alerts():
            _LOGGER.debug(f'[create_jobs_by_domain] Push task (JobService.create): {domain_id}')
            self.job_mgr.push_task('monitoring_alert_job', 'JobService', 'create', {'domain_id': domain_id})

    def _list_domains_of_alerts(self):
        query = {
            'distinct': 'domain_id',
            'filter': [
                {
                    'k': 'state',
                    'v': ['TRIGGERED', 'ACKNOWLEDGED'],
                    'o': 'in'
                }
            ]
        }

        alert_mgr: AlertManager = self.locator.get_manager('AlertManager')

        response = alert_mgr.stat_alerts(query)
        return response.get('results', [])
