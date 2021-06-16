import logging
import copy

from spaceone.core.service import *
from spaceone.core import cache
from spaceone.core import utils
from spaceone.monitoring.error.webhook import *
from spaceone.monitoring.model.event_model import Event
from spaceone.monitoring.model.webhook_model import Webhook
from spaceone.monitoring.model.project_alert_config_model import ProjectAlertConfig
from spaceone.monitoring.model.escalation_policy_model import EscalationPolicy
from spaceone.monitoring.manager.alert_manager import AlertManager
from spaceone.monitoring.manager.webhook_manager import WebhookManager
from spaceone.monitoring.manager.event_manager import EventManager
from spaceone.monitoring.manager.webhook_plugin_manager import WebhookPluginManager
from spaceone.monitoring.manager.project_alert_config_manager import ProjectAlertConfigManager

_LOGGER = logging.getLogger(__name__)


@authentication_handler
@authorization_handler
@mutation_handler
@event_handler
class EventService(BaseService):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.event_mgr: EventManager = self.locator.get_manager('EventManager')

    @transaction(append_meta={'authorization.scope': 'PROJECT'})
    @check_required(['webhook_id', 'access_key', 'data'])
    def create(self, params):
        """Create event

        Args:
            params (dict): {
                'webhook_id': 'str',
                'access_key': 'str',
                'data': 'str'
            }

        Returns:
            event_vo (object)
        """

        webhook_data = self._get_webhook_data(params['webhook_id'])

        self._check_access_key(params['access_key'], webhook_data['access_key'])
        self._check_webhook_state(webhook_data)

        webhook_plugin_mgr: WebhookPluginManager = self.locator.get_manager('WebhookPluginManager')
        webhook_plugin_mgr.initialize(webhook_data['plugin_id'], webhook_data['plugin_version'],
                                      webhook_data['domain_id'])
        response = webhook_plugin_mgr.parse_event(webhook_data['plugin_options'], params['data'])

        for event_data in response.get('results', []):
            # Check event data using schematics
            self._create_event(event_data, params['data'], webhook_data)

    @transaction(append_meta={'authorization.scope': 'PROJECT'})
    @check_required(['event_id', 'domain_id'])
    def get(self, params):
        """ Get event

        Args:
            params (dict): {
                'event_id': 'str',
                'domain_id': 'str',
                'only': 'list
            }

        Returns:
            event_vo (object)
        """

        return self.event_mgr.get_event(params['event_id'], params['domain_id'], params.get('only'))

    @transaction(append_meta={
        'authorization.scope': 'PROJECT',
        'mutation.append_parameter': {'user_projects': 'authorization.projects'}
    })
    @check_required(['domain_id'])
    @append_query_filter(['event_id', 'event_key', 'event_type', 'severity', 'resource_id', 'alert_id',
                          'webhook_id', 'project_id', 'domain_id', 'user_projects'])
    @append_keyword_filter(['event_id', 'title'])
    def list(self, params):
        """ List events

        Args:
            params (dict): {
                'event_id': 'str',
                'event_key': 'str',
                'event_type': 'str',
                'severity': 'str',
                'resource_id': 'str',
                'alert_id': 'str',
                'webhook_id': 'str',
                'project_id': 'str',
                'domain_id': 'str',
                'query': 'dict (spaceone.api.core.v1.Query)',
                'user_projects': 'list', // from meta
            }

        Returns:
            event_vos (object)
            total_count
        """

        query = params.get('query', {})
        return self.event_mgr.list_events(query)

    @transaction(append_meta={
        'authorization.scope': 'PROJECT',
        'mutation.append_parameter': {'user_projects': 'authorization.projects'}
    })
    @check_required(['query', 'domain_id'])
    @append_query_filter(['domain_id', 'user_projects'])
    @append_keyword_filter(['event_id', 'title'])
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
        return self.event_mgr.stat_events(query)

    @cache.cacheable(key='webhook-data:{webhook_id}', expire=300)
    def _get_webhook_data(self, webhook_id):
        webhook_mgr: WebhookManager = self.locator.get_manager('WebhookManager')
        webhook_vo: Webhook = webhook_mgr.get_webhook_by_id(webhook_id)
        return {
            'webhook_id': webhook_vo.webhook_id,
            'project_id': webhook_vo.project_id,
            'domain_id': webhook_vo.domain_id,
            'state': webhook_vo.state,
            'access_key': webhook_vo.access_key,
            'plugin_id': webhook_vo.plugin_info.plugin_id,
            'plugin_version': webhook_vo.plugin_info.version,
            'plugin_options': webhook_vo.plugin_info.options
        }

    @staticmethod
    def _check_access_key(request_access_key, webhook_access_key):
        if request_access_key != webhook_access_key:
            raise ERROR_PERMISSION_DENIED()

    @staticmethod
    def _check_webhook_state(webhook_data):
        if webhook_data['state'] == 'DISABLED':
            raise ERROR_WEBHOOK_STATE_DISABLED(webhook_id=webhook_data['webhook_id'])

    def _create_event(self, event_data, raw_data, webhook_data):
        event_data['raw_data'] = copy.deepcopy(raw_data)
        event_data['occurred_at'] = utils.iso8601_to_datetime(event_data.get('occurred_at'))
        event_data['webhook_id'] = webhook_data['webhook_id']
        event_data['project_id'] = webhook_data['project_id']
        event_data['domain_id'] = webhook_data['domain_id']

        # Change event data by event rule

        event_key = event_data['event_key']

        # Check resolved event
        event_vo = self.event_mgr.get_event_by_key(event_key)

        if event_vo is None:
            alert_vo = self._create_alert(event_data)
            event_data['alert_id'] = alert_vo.alert_id
            event_data['alert'] = alert_vo

        else:
            event_data['alert_id'] = event_vo.alert_id
            event_data['alert'] = event_vo.alert

        self.event_mgr.create_event(event_data)

    def _create_alert(self, event_data):
        alert_mgr: AlertManager = self.locator.get_manager('AlertManager')

        alert_data = copy.deepcopy(event_data)
        alert_data['urgency'] = self._get_urgency_from_severity(event_data['severity'])

        escalation_policy_id, escalation_ttl = self._get_escalation_policy_info(event_data['project_id'],
                                                                                event_data['domain_id'])

        alert_data['escalation_policy_id'] = escalation_policy_id
        alert_data['escalation_ttl'] = escalation_ttl

        return alert_mgr.create_alert(alert_data)

    @staticmethod
    def _get_urgency_from_severity(severity):
        if severity in ['CRITICAL', 'ERROR', 'NOT_AVAILABLE']:
            return 'HIGH'
        else:
            return 'LOW'

    @cache.cacheable(key='escalation-policy-info:{domain_id}:{project_id}', expire=60)
    def _get_escalation_policy_info(self, project_id, domain_id):
        project_alert_config_vo: ProjectAlertConfig = self._get_project_alert_config(project_id, domain_id)
        escalation_policy_vo: EscalationPolicy = project_alert_config_vo.escalation_policy

        return escalation_policy_vo.escalation_policy_id, escalation_policy_vo.repeat_count

    def _update_alert_state(self, event_type, alert_vo, project_id, domain_id):
        if event_type == 'RECOVERY':
            if self._is_auto_recovery(project_id, domain_id) and alert_vo.state != 'RESOLVED':
                alert_mgr: AlertManager = self.locator.get_manager('AlertManager')
                alert_mgr.update_alert_by_vo({'state': 'RESOLVED'}, alert_vo)

    @cache.cacheable(key='auto-recovery:{domain_id}:{project_id}', expire=60)
    def _is_auto_recovery(self, project_id, domain_id):
        project_alert_config_vo: ProjectAlertConfig = self._get_escalation_policy(project_id, domain_id)
        return project_alert_config_vo.options.auto_recovery

    def _get_project_alert_config(self, project_id, domain_id):
        project_alert_config_mgr: ProjectAlertConfigManager = self.locator.get_manager('ProjectAlertConfigManager')
        return project_alert_config_mgr.get_project_alert_config(project_id, domain_id)