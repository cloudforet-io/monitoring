import logging
import time

from spaceone.core.service import *
from spaceone.core import queue, utils

_LOGGER = logging.getLogger(__name__)


@authentication_handler
@authorization_handler
@mutation_handler
@event_handler
class DomainService(BaseService):

    @transaction(append_meta={'authorization.scope': 'SYSTEM'})
    def list(self, params):
        """ List alert notes

        Args:
            params (dict): {}

        Returns:
            None
        """

        print(f"Call DomainService.list {str(params)}", self.transaction.id)

        """
        task_sample = {
            'name': 'monitoring_alert_schedule',
            'version': 'v1',
            'executionEngine': 'BaseWorker',
            'stages': [{
                'locator': 'SERVICE',
                'name': 'DomainService',
                'metadata': self._metadata,
                'method': 'list',
                'params': {
                    'params': {
                        'from': 'monitoring_alert_scheduler'
                    }
                }
            }]
        }
        """

        task = {
            'name': 'monitoring_alert_schedule_recursive',
            'version': 'v1',
            'executionEngine': 'BaseWorker',
            'stages': [{
                'locator': 'SERVICE',
                'name': 'DomainService',
                'metadata': self.transaction.meta,
                'method': 'list2',
                'params': {
                    'params': {
                        'from': 'DomainService.list'
                    }
                }
            }]
        }

        queue.put('monitoring_q', utils.dump_json(task))

    @transaction(append_meta={'authorization.scope': 'SYSTEM'})
    def list2(self, params):
        """ List alert notes

        Args:
            params (dict): {}

        Returns:
            None
        """

        print(f"Call DomainService.list2 {str(params)}", self.transaction.id)
