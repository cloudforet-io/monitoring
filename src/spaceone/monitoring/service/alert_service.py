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

        if alert_vo.state != state and state == 'RESOLVED' and status_message is None:
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

        Args:
            params (dict): {
                'alerts': 'list',
                'merge_to': 'str',
                'domain_id': 'str',
            }

        Returns:
            alert_vo (object)
        """
        merge_to = params['merge_to']
        alerts = params['alerts']
        domain_id = params['domain_id']

        self._check_merge_condition(merge_to=merge_to, alert_ids=alerts)
        alerts.remove(merge_to)

        events = []

        for alert_id in alerts:
            event_vos = self.event_mgr.filter_events(alert_id=alert_id, domain_id=domain_id)
            events += event_vos

        alert_vo = self.alert_mgr.get_alert(merge_to, domain_id)
        update_event_params = {'alert_id': merge_to, 'alert': alert_vo}

        for event_vo in events:
            self.event_mgr.update_event_by_vo(params=update_event_params, event_vo=event_vo)

        for alert_id in alerts:
            self.alert_mgr.delete_alert(alert_id=alert_id, domain_id=params['domain_id'])

        return alert_vo

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

    @staticmethod
    def _check_merge_condition(merge_to, alert_ids):
        if merge_to not in alert_ids:
            raise ERROR_MERGE_ALERT_NOT_EXIST(alert_id=merge_to)