import logging
from datetime import datetime

from spaceone.core.service import *
from spaceone.core import cache, config
from spaceone.monitoring.error.alert import *
from spaceone.monitoring.model.alert_model import Alert
from spaceone.monitoring.model.project_alert_config_model import ProjectAlertConfig
from spaceone.monitoring.model.escalation_policy_model import EscalationPolicy
from spaceone.monitoring.manager.project_alert_config_manager import ProjectAlertConfigManager
from spaceone.monitoring.manager.escalation_policy_manager import EscalationPolicyManager
from spaceone.monitoring.manager.alert_manager import AlertManager
from spaceone.monitoring.manager.event_manager import EventManager
from spaceone.monitoring.manager.job_manager import JobManager

_LOGGER = logging.getLogger(__name__)


@authentication_handler(exclude=['update_state'])
@authorization_handler(exclude=['update_state'])
@mutation_handler
@event_handler
class AlertService(BaseService):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.alert_mgr: AlertManager = self.locator.get_manager('AlertManager')
        self.event_mgr: EventManager = self.locator.get_manager('EventManager')

    @transaction(append_meta={'authorization.scope': 'PROJECT'})
    @check_required(['title', 'project_id', 'domain_id'])
    def create(self, params):
        """Create alert

        Args:
            params (dict): {
                'title': 'str',
                'description': 'str',
                'assignee': 'str',
                'urgency': 'str',
                'project_id': 'str',
                'domain_id': 'str'
            }

        Returns:
            alert_vo (object)
        """

        project_id = params['project_id']
        domain_id = params['domain_id']

        project_alert_config_mgr: ProjectAlertConfigManager = self.locator.get_manager('ProjectAlertConfigManager')

        project_alert_config_vo: ProjectAlertConfig = project_alert_config_mgr.get_project_alert_config(project_id,
                                                                                                        domain_id)
        escalation_policy_vo: EscalationPolicy = project_alert_config_vo.escalation_policy

        params['escalation_policy_id'] = escalation_policy_vo.escalation_policy_id
        params['escalation_ttl'] = escalation_policy_vo.repeat_count + 1
        params['escalated_at'] = None

        # TODO: Check Assignee

        params['triggered_by'] = self.transaction.get_meta('user_id')

        alert_vo = self.alert_mgr.create_alert(params)

        self._create_notification(alert_vo, 'create_alert_notification')

        return alert_vo

    @transaction(append_meta={'authorization.scope': 'PROJECT'})
    @check_required(['alert_id', 'domain_id'])
    def update(self, params):
        """Update alert

        Args:
            params (dict): {
                'alert_id': 'str',
                'title': 'str',
                'state': 'str',
                'status_message': 'str',
                'description': 'str',
                'assignee': 'str',
                'urgency': 'str',
                'project_id': 'str',
                'reset_status_message': 'bool',
                'reset_description': 'bool',
                'reset_assignee': 'bool',
                'domain_id': 'str'
            }

        Returns:
            alert_vo (object)
        """
        
        alert_id = params['alert_id']
        domain_id = params['domain_id']
        project_id = params.get('project_id')
        state = params.get('state')
        assignee = params.get('assignee')
        status_message = params.get('status_message')
        reset_status_message = params.get('reset_status_message', False)
        reset_description = params.get('reset_description', False)
        reset_assignee = params.get('reset_assignee', False)

        is_resolved_notify = False
        is_assignee_notify = False

        if project_id:
            project_alert_config_mgr: ProjectAlertConfigManager = self.locator.get_manager('ProjectAlertConfigManager')

            project_alert_config_vo: ProjectAlertConfig = project_alert_config_mgr.get_project_alert_config(project_id,
                                                                                                            domain_id)
            escalation_policy_vo: EscalationPolicy = project_alert_config_vo.escalation_policy

            params['escalation_policy_id'] = escalation_policy_vo.escalation_policy_id
            params['escalation_ttl'] = escalation_policy_vo.repeat_count
            params['escalation_step'] = 1
            params['escalated_at'] = None
            params['assignee'] = None
            assignee = None

        if state:
            if state == 'ACKNOWLEDGED':
                params['acknowledged_at'] = datetime.utcnow()
                params['resolved_at'] = None
            elif state == 'RESOLVED':
                params['escalation_ttl'] = 0
                params['resolved_at'] = datetime.utcnow()
            elif state == 'TRIGGERED':
                params['acknowledged_at'] = None
                params['resolved_at'] = None

        alert_vo = self.alert_mgr.get_alert(alert_id, domain_id)

        if alert_vo.state == 'ERROR':
            raise ERROR_INVALID_PARAMETER(key='state', reason='The error state cannot be changed.')

        if alert_vo.state != state and status_message is None:
            params['status_message'] = ''

        if reset_status_message:
            params['status_message'] = ''

        if reset_description:
            params['description'] = ''

        if reset_assignee:
            params['assignee'] = None
            assignee = None

        if assignee:
            # TODO: Check Assignee
            is_assignee_notify = True

        if alert_vo.state in ['TRIGGERED', 'ACKNOWLEDGED'] and state == 'RESOLVED':
            is_resolved_notify = True

        updated_alert_vo: Alert = self.alert_mgr.update_alert_by_vo(params, alert_vo)

        if is_resolved_notify:
            self._create_notification(updated_alert_vo, 'create_resolved_notification')
        elif is_assignee_notify and updated_alert_vo.state in ['TRIGGERED', 'ACKNOWLEDGED']:
            self._create_notification(updated_alert_vo, 'create_assigned_notification', assignee)

        return updated_alert_vo

    @transaction
    @check_required(['alert_id', 'access_key', 'state'])
    def update_state(self, params):
        """Update alert state

        Args:
            params (dict): {
                'alert_id': 'str',
                'access_key': 'str',
                'state': 'str'
            }

        Returns:
            alert_vo (object)
        """
        alert_id = params['alert_id']
        access_key = params['access_key']
        state = params['state']

        is_resolved_notify = False

        # Check Access Key
        domain_id = self._check_access_key(alert_id, access_key)

        # Check State
        self._check_state(state)

        alert_vo = self.alert_mgr.get_alert(alert_id, domain_id)

        if alert_vo.state == 'ERROR':
            raise ERROR_INVALID_PARAMETER(key='state', reason='The error state cannot be changed.')

        if alert_vo.state != 'TRIGGERED':
            # raise ERROR_ALERT_ALREADY_PROCESSED(alert_id=alert_id)
            return alert_vo

        update_params = {
            'state': state
        }

        if state == 'ACKNOWLEDGED':
            update_params['acknowledged_at'] = datetime.utcnow()
        elif state == 'RESOLVED':
            update_params['resolved_at'] = datetime.utcnow()

        if alert_vo.state in ['TRIGGERED', 'ACKNOWLEDGED'] and state == 'RESOLVED':
            is_resolved_notify = True

        updated_alert_vo = self.alert_mgr.update_alert_by_vo(update_params, alert_vo)

        if is_resolved_notify:
            self._create_notification(updated_alert_vo, 'create_resolved_notification')

        return updated_alert_vo

    @transaction(append_meta={'authorization.scope': 'PROJECT'})
    @check_required(['alerts', 'merge_to', 'domain_id'])
    def merge(self, params):
        """Merge alerts
1
        Args: # Question?
            params (dict): {
                'alerts': 'list',
                'merge_to': 'str',
                'domain_id': 'str',
                'events' :'list'
            }

        Returns:
            alert_vo (object)
        """
        '''
           Plan 
           1. merge_to가 params로 들어온 alerts 에 들어있는지 확인 > 아니면 raise => alert_service 
           2. params의 나머지 alerts 들 돌면서 딸린 event 자식들 검색 => alert_service
           3. event들의 alert_id를 merge_to ID로 바꿔줌 => alert_manager.merge 에서 하고싶은데.. / event_mgr 호출 못함 -> alert_service에서 하고..
           4. merge_to를 제외한 alerts 삭제 => alert_manager.merge(params)
           -------
           rollback 에 관한 의문점 
           1-1. transaction 은 어디서부터 시작해 어디서 끝나는가? transaction 에 관한 설명 need
           1-2. (event_mgr) child event 검색에 실패했을 때 / (event_mgr) alert_id를 merge_to ID로 바꿔줬을 때 / merge_to를 제외한 alerts 를 삭제하는 도중에
           모두 롤백해야하는데 add_rollback에 3개를 등록하는 것인가?
           2. 왜 merge API 의 return은 {alert_info}인가? 왜? Flag 값은 없는..?
           -------
           왜 개별 parameter로 명시해서 넘기지 않고 params 에 담아서 넘기지? -> No reason
        '''
        merge_to = params['merge_to']
        alerts = params['alerts']
        alert_ids = []
        for alert in alerts:
            alert_ids.append(alert['alert_id'])

        if self._check_merge_condition(merge_to=merge_to, alert_ids=alert_ids):
            for alert in alerts:
                if alert['alert_id'] != merge_to:
                    alert_ids.append(alert['alert_id'])

            events = []
            for alert_id in alert_ids:
                event_vos = self._list_events_by_alert_id(alert_id=alert_id)  # List child events
                events.append(event_vos)

            print(f'events: {events}')
            event_params = {
                'alert_id': merge_to
            }

            for event_vo in events:
                self.event_mgr.update_event_by_vo(params=event_params, event_vo=event_vo)

            params['events'] = events
            params['deleted_alerts'] = alert_ids
            return self.alert_mgr.merge_alerts(params, merge_to)
        else:
            raise ERROR_MERGE_ALERT_NOT_EXIST(alert_id=merge_to)

    @transaction(append_meta={'authorization.scope': 'PROJECT'})
    @check_required(['alert_id', 'end_time', 'domain_id'])
    @change_timestamp_value(['end_time'], timestamp_format='iso8601')
    def snooze(self, params):
        """Snooze alert

        Args:
            params (dict): {
                'alert_id': 'str',
                'end_time': 'str',
                'domain_id': 'str'
            }

        Returns:
            alert_vo (object)
        """

        alert_id = params['alert_id']
        domain_id = params['domain_id']

        alert_vo = self.alert_mgr.get_alert(alert_id, domain_id)

        # TODO: Check end_times

        params['is_snoozed'] = True
        params['snoozed_end_time'] = params['end_time']

        return self.alert_mgr.update_alert_by_vo(params, alert_vo)

    @transaction(append_meta={'authorization.scope': 'PROJECT'})
    @check_required(['alert_id', 'resource_type', 'resource_id', 'domain_id'])
    def add_responder(self, params):
        """Add alert responder

        Args:
            params (dict): {
                'alert_id': 'str',
                'resource_type': 'str',
                'resource_id': 'str',
                'domain_id': 'str'
            }

        Returns:
            alert_vo (object)
        """

        # TODO: Check resource_type and resource_id

        return self.alert_mgr.add_responder(params)

    @transaction(append_meta={'authorization.scope': 'PROJECT'})
    @check_required(['alert_id', 'resource_type', 'resource_id', 'domain_id'])
    def remove_responder(self, params):
        """Remove alert responder

        Args:
            params (dict): {
                'alert_id': 'str',
                'resource_type': 'str',
                'resource_id': 'str',
                'domain_id': 'str'
            }

        Returns:
            alert_vo (object)
        """

        return self.alert_mgr.remove_responder(params)

    @transaction(append_meta={'authorization.scope': 'PROJECT'})
    @check_required(['alert_id', 'project_id', 'domain_id'])
    def add_project_dependency(self, params):
        """Add dependent project

        Args:
            params (dict): {
                'alert_id': 'str',
                'project_id': 'str',
                'domain_id': 'str'
            }

        Returns:
            alert_vo (object)
        """

        # TODO: Check project_id

        return self.alert_mgr.add_project_dependency(params)

    @transaction(append_meta={'authorization.scope': 'PROJECT'})
    @check_required(['alert_id', 'project_id', 'domain_id'])
    def remove_project_dependency(self, params):
        """Remove dependent project

        Args:
            params (dict): {
                'alert_id': 'str',
                'project_id': 'str',
                'domain_id': 'str'
            }

        Returns:
            alert_vo (object)
        """

        return self.alert_mgr.remove_project_dependency(params)

    @transaction(append_meta={'authorization.scope': 'PROJECT'})
    @check_required(['alert_id', 'domain_id'])
    def delete(self, params):
        """Delete alert

        Args:
            params (dict): {
                'alert_id': 'str',
                'domain_id': 'str'
            }

        Returns:
            None
        """

        self.alert_mgr.delete_alert(params['alert_id'], params['domain_id'])

    @transaction(append_meta={'authorization.scope': 'PROJECT'})
    @check_required(['alert_id', 'domain_id'])
    def get(self, params):
        """ Get alert

        Args:
            params (dict): {
                'alert_id': 'str',
                'domain_id': 'str',
                'only': 'list
            }

        Returns:
            alert_vo (object)
        """

        return self.alert_mgr.get_alert(params['alert_id'], params['domain_id'], params.get('only'))

    @transaction(append_meta={
        'authorization.scope': 'PROJECT',
        'mutation.append_parameter': {'user_projects': 'authorization.projects'}
    })
    @check_required(['domain_id'])
    @append_query_filter(['alert_number', 'alert_id', 'title', 'state', 'assignee', 'urgency', 'severity', 'is_snoozed',
                          'resource_id', 'triggered_by', 'webhook_id', 'escalation_policy_id', 'project_id',
                          'domain_id', 'user_projects'])
    @append_keyword_filter(['alert_id', 'title'])
    def list(self, params):
        """ List alerts

        Args:
            params (dict): {
                'alert_number': 'str',
                'alert_id': 'str',
                'title': 'str',
                'state': 'str',
                'assignee': 'str',
                'urgency': 'str',
                'severity': 'str',
                'is_snoozed': 'bool',
                'resource_id': 'str',
                'webhook_id': 'bool',
                'escalation_policy_id': 'str',
                'project_id': 'str',
                'domain_id': 'str',
                'query': 'dict (spaceone.api.core.v1.Query)',
                'user_projects': 'list', // from meta
            }

        Returns:
            alert_vos (object)
            total_count
        """

        query = params.get('query', {})
        return self.alert_mgr.list_alerts(query)

    @transaction(append_meta={
        'authorization.scope': 'PROJECT',
        'mutation.append_parameter': {'user_projects': 'authorization.projects'}
    })
    @check_required(['query', 'domain_id'])
    @append_query_filter(['domain_id', 'user_projects'])
    @append_keyword_filter(['alert_id', 'title'])
    def stat(self, params):
        """
        Args:
            params (dict): {
                'domain_id': 'str',
                'query': 'dict (spaceone.api.core.v1.StatisticsQuery)',
                'user_projects': 'list', // from meta
            }

        Returns:
            values (list) : 'list of statistics data'

        """

        query = params.get('query', {})
        return self.alert_mgr.stat_alerts(query)

    def _create_notification(self, alert_vo: Alert, method, user_id=None):
        params = {
            'alert_id': alert_vo.alert_id,
            'domain_id': alert_vo.domain_id
        }

        if user_id:
            params['user_id'] = user_id

        job_mgr: JobManager = self.locator.get_manager('JobManager')
        job_mgr.push_task(
            'monitoring_alert_notification_from_manual',
            'JobService',
            method,
            params
        )

    @staticmethod
    def _check_access_key(alert_id, access_key):
        domain_id = cache.get(f'alert-notification-callback:{alert_id}:{access_key}')

        if domain_id is None:
            raise ERROR_PERMISSION_DENIED()

        return domain_id

    @staticmethod
    def _check_state(state):
        if state not in ['ACKNOWLEDGED', 'RESOLVED']:
            raise ERROR_INVALID_PARAMETER(key='state', reason='Unsupported state. (ACKNOWLEDGED | RESOLVED)')

    def _list_events_by_alert_id(self, alert_id):
        query = {
            'filter': [
                {
                    'k': 'alert_id',
                    'v': alert_id,
                    'o': 'eq'
                }
            ],
            'sort': {
                'key': 'created_at',
                'desc': True
            }
        }
        event_vos, total_count = self.event_mgr.list_events(query)
        return event_vos

    @staticmethod
    def _check_merge_condition(merge_to, alert_ids):
        if merge_to in alert_ids:
            return True
        else:
            return False
