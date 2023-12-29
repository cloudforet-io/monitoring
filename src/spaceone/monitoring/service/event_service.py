import copy
import logging
from datetime import datetime

from spaceone.core import utils, cache, config
from spaceone.core.service import *

from spaceone.monitoring.error.webhook import *
from spaceone.monitoring.manager import PluginManager
from spaceone.monitoring.manager.alert_manager import AlertManager
from spaceone.monitoring.manager.event_manager import EventManager
from spaceone.monitoring.manager.event_rule_manager import EventRuleManager
from spaceone.monitoring.manager.job_manager import JobManager
from spaceone.monitoring.manager.project_alert_config_manager import (
    ProjectAlertConfigManager,
)
from spaceone.monitoring.manager.webhook_manager import WebhookManager
from spaceone.monitoring.manager.webhook_plugin_manager import WebhookPluginManager
from spaceone.monitoring.model.alert_model import Alert
from spaceone.monitoring.model.escalation_policy_model import EscalationPolicy
from spaceone.monitoring.model.event_model import Event
from spaceone.monitoring.model.project_alert_config_model import ProjectAlertConfig
from spaceone.monitoring.model.webhook_model import Webhook

_LOGGER = logging.getLogger(__name__)


@authentication_handler
@authorization_handler
@mutation_handler
@event_handler
class EventService(BaseService):
    resource = "Event"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.resource = "Event"
        self.event_mgr: EventManager = self.locator.get_manager(EventManager)
        self.webhook_mgr: WebhookManager = self.locator.get_manager(WebhookManager)
        self.webhook_plugin_mgr: WebhookPluginManager = self.locator.get_manager(
            WebhookPluginManager
        )

    @transaction(exclude=["authentication", "authorization", "mutation"])
    @check_required(["webhook_id", "access_key", "data"])
    def create(self, params: dict) -> None:
        """Create event

        Args:
            params (dict): {
                'webhook_id': 'str',    # required
                'access_key': 'str',    # required
                'data': 'str'           # required
            }

        Returns:
            event_vo (object)
        """

        webhook_data = self._get_webhook_data(params["webhook_id"])

        self._check_access_key(params["access_key"], webhook_data["access_key"])
        self._check_webhook_state(webhook_data)

        try:
            webhook_plugin_mgr: WebhookPluginManager = self.locator.get_manager(
                WebhookPluginManager
            )

            plugin_info = {
                "plugin_id": webhook_data["plugin_id"],
                "version": webhook_data["plugin_version"],
                "upgrade_mode": webhook_data["plugin_upgrade_mode"],
            }
            plugin_mgr: PluginManager = self.locator.get_manager(PluginManager)
            endpoint, updated_version = plugin_mgr.get_plugin_endpoint(
                plugin_info, webhook_data["domain_id"]
            )

            if updated_version:
                _LOGGER.debug(
                    f'[create] upgrade plugin version: {webhook_data["plugin_version"]} -> {updated_version}'
                )
                webhook_vo: Webhook = self.webhook_mgr.get_webhook(
                    webhook_data["webhook_id"], webhook_data["domain_id"]
                )

                plugin_info = webhook_vo.plugin_info.to_dict()
                plugin_metadata = self.webhook_plugin_mgr.init_plugin(
                    endpoint, plugin_info.get("options", {})
                )
                plugin_info["version"] = updated_version
                plugin_info["metadata"] = plugin_metadata
                self.webhook_mgr.update_webhook_by_vo(
                    {"plugin_info": plugin_info}, webhook_vo
                )

            response = webhook_plugin_mgr.parse_event(
                endpoint, webhook_data["plugin_options"], params["data"]
            )

        except Exception as e:
            if not isinstance(e, ERROR_BASE):
                e = ERROR_UNKNOWN(message=str(e))

            _LOGGER.error(f"[create] Event parsing failed: {e.message}", exc_info=True)
            response = self._create_error_event(webhook_data["name"], e.message)

        for event_data in response.get("results", []):
            # TODO: Check event data using schematics

            _LOGGER.debug(f"[Event.create] event_data: {event_data}")
            self._create_event(event_data, params["data"], webhook_data)

    @transaction(
        permission="monitoring:Event.read",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @check_required(["event_id", "domain_id"])
    def get(self, params):
        """Get event

        Args:
            params (dict): {
                'event_id': 'str',    # required
                'domain_id': 'str',   # injected from auth (required)
            }

        Returns:
            event_vo (object)
        """

        event_id = params["event_id"]
        domain_id = params["domain_id"]
        workspace_id = params.get("workspace_id")
        user_projects = params.get("user_projects")

        return self.event_mgr.get_event(
            event_id, domain_id, workspace_id, user_projects
        )

    @transaction(
        permission="monitoring:Event.read",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @check_required(["domain_id"])
    @append_query_filter(
        [
            "event_id",
            "event_key",
            "event_type",
            "severity",
            "resource_id",
            "alert_id",
            "webhook_id",
            "project_id",
            "workspace_id" "domain_id",
            "user_projects",
        ]
    )
    @append_keyword_filter(["event_id", "title"])
    def list(self, params):
        """List events

        Args:
            params (dict): {
                'query': 'dict (spaceone.api.core.v1.Query)',
                'event_id': 'str',
                'event_key': 'str',
                'event_type': 'str',
                'severity': 'str',
                'resource_id': 'str',
                'alert_id': 'str',
                'webhook_id': 'str',
                'project_id': 'str',
                'workspace_id': 'str',
                'domain_id': 'str',         # injected from auth (required)
                'user_projects': 'list',    # injected from auth
            }

        Returns:
            event_vos (object)
            total_count
        """

        query = params.get("query", {})
        return self.event_mgr.list_events(query)

    @transaction(
        permission="monitoring:Event.read",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @check_required(["query", "domain_id"])
    @append_query_filter(["domain_id", "workspace_id", "user_projects"])
    @append_keyword_filter(["event_id", "title"])
    def stat(self, params):
        """
        Args:
            params (dict): {
                'query': 'dict (spaceone.api.core.v1.StatisticsQuery)',
                'domain_id': 'str',         # injected from auth (required)
                'workspace_id': 'str',      # injected from auth
                'user_projects': 'list',    # injected from auth

            }

        Returns:
            values (list) : 'list of statistics data'

        """

        query = params.get("query", {})
        return self.event_mgr.stat_events(query)

    @cache.cacheable(key="webhook-data:{webhook_id}", expire=300)
    def _get_webhook_data(self, webhook_id):
        webhook_vo: Webhook = self.webhook_mgr.get_webhook_by_id(webhook_id)
        return {
            "webhook_id": webhook_vo.webhook_id,
            "name": webhook_vo.name,
            "project_id": webhook_vo.project_id,
            "workspace_id": webhook_vo.workspace_id,
            "domain_id": webhook_vo.domain_id,
            "state": webhook_vo.state,
            "access_key": webhook_vo.access_key,
            "plugin_id": webhook_vo.plugin_info.plugin_id,
            "plugin_version": webhook_vo.plugin_info.version,
            "plugin_upgrade_mode": webhook_vo.plugin_info.upgrade_mode,
            "plugin_options": webhook_vo.plugin_info.options,
        }

    @staticmethod
    def _check_access_key(request_access_key, webhook_access_key):
        if request_access_key != webhook_access_key:
            raise ERROR_PERMISSION_DENIED()

    @staticmethod
    def _check_webhook_state(webhook_data):
        if webhook_data["state"] == "DISABLED":
            raise ERROR_WEBHOOK_STATE_DISABLED(webhook_id=webhook_data["webhook_id"])

    def _create_event(self, event_data, raw_data, webhook_data):
        event_data["raw_data"] = copy.deepcopy(raw_data)
        event_data["occurred_at"] = utils.iso8601_to_datetime(
            event_data.get("occurred_at")
        )
        event_data["webhook_id"] = webhook_data["webhook_id"]
        event_data["project_id"] = webhook_data["project_id"]
        event_data["workspace_id"] = webhook_data["workspace_id"]
        event_data["domain_id"] = webhook_data["domain_id"]
        event_data["severity"] = event_data.get("severity", "NONE")
        event_data["account"] = event_data.get("account", "")
        event_data["provider"] = event_data.get("provider", "")

        event_rule_mgr: EventRuleManager = self.locator.get_manager("EventRuleManager")

        # Change event data by event rule
        event_data = event_rule_mgr.change_event_data(
            event_data,
            webhook_data["project_id"],
            webhook_data["domain_id"],
            webhook_data["workspace_id"],
        )

        event_vo: Event = self.event_mgr.get_event_by_key(
            event_data["event_key"],
            event_data["domain_id"],
            event_data["project_id"],
            event_data["workspace_id"],
        )

        if event_vo and event_vo.alert.state != "RESOLVED":
            self._update_alert(event_vo.alert, event_data)

            event_data["alert_id"] = event_vo.alert_id
            event_data["alert"] = event_vo.alert
        else:
            # Skip health event
            if event_data["event_type"] == "RECOVERY":
                _LOGGER.debug(
                    f'[_create_event] Skip health event: {event_data.get("title")} (event_type = RECOVERY)'
                )
                return None

            # Create new alert
            _LOGGER.debug(
                f'[_create_event] Create new alert: {event_data.get("title")} '
                f'(event_type = {event_data["event_type"]})'
            )
            alert_vo = self._create_alert(event_data)

            event_data["alert_id"] = alert_vo.alert_id
            event_data["alert"] = alert_vo

        self.event_mgr.create_event(event_data)

    # create alert by system
    def _create_alert(self, event_data):
        alert_mgr: AlertManager = self.locator.get_manager("AlertManager")

        alert_data = copy.deepcopy(event_data)

        if "urgency" in event_data:
            alert_data["urgency"] = event_data["urgency"]
        else:
            alert_data["urgency"] = self._get_urgency_from_severity(
                event_data["severity"]
            )

        escalation_policy_id, escalation_ttl = self._get_escalation_policy_info(
            event_data["project_id"],
            event_data["workspace_id"],
            event_data["domain_id"],
        )

        alert_data["escalation_policy_id"] = escalation_policy_id

        if event_data.get("no_notification", False):
            alert_data["escalation_ttl"] = 0
        else:
            alert_data["escalation_ttl"] = escalation_ttl + 1

        alert_data["triggered_by"] = alert_data["webhook_id"]

        if event_data.get("event_type", "ERROR") == "ERROR":
            alert_data["state"] = "ERROR"

        alert_vo = alert_mgr.create_alert(alert_data)

        self._create_notification(
            alert_vo.alert_id, alert_vo.domain_id, "create_alert_notification"
        )

        return alert_vo

    @staticmethod
    def _get_urgency_from_severity(severity):
        if severity in ["CRITICAL", "ERROR", "NOT_AVAILABLE"]:
            return "HIGH"
        else:
            return "LOW"

    @cache.cacheable(key="escalation-policy-info:{domain_id}:{project_id}", expire=300)
    def _get_escalation_policy_info(self, project_id, workspace_id, domain_id):
        project_alert_config_vo: ProjectAlertConfig = self._get_project_alert_config(
            project_id, workspace_id, domain_id
        )
        escalation_policy_vo: EscalationPolicy = (
            project_alert_config_vo.escalation_policy
        )

        return (
            escalation_policy_vo.escalation_policy_id,
            escalation_policy_vo.repeat_count,
        )

    def _update_alert(self, alert_vo: Alert, event_data: dict) -> None:
        # Resolve alert when receiving recovery event
        alert_id = alert_vo.alert_id
        domain_id = alert_vo.domain_id

        alert_mgr: AlertManager = self.locator.get_manager("AlertManager")
        update_params = {"description": event_data.get("description", "")}

        is_resolved = self._check_resolved_state(event_data, alert_vo)

        if is_resolved:
            update_params["state"] = "RESOLVED"
            update_params["resolved_at"] = datetime.utcnow()

        alert_mgr.update_alert_by_vo(update_params, alert_vo)

        if is_resolved:
            self._create_notification(
                alert_id, domain_id, "create_resolved_notification"
            )

    def _check_resolved_state(self, event_data: dict, alert_vo: Alert) -> bool:
        if (
            event_data["event_type"] == "RECOVERY"
            and alert_vo.state != "RESOLVED"
            and self._is_auto_recovery(
                alert_vo.project_id, alert_vo.workspace_id, alert_vo.domain_id
            )
        ):
            return True
        else:
            return False

    @cache.cacheable(key="auto-recovery:{domain_id}:{project_id}", expire=300)
    def _is_auto_recovery(self, project_id, workspace_id, domain_id):
        project_alert_config_vo: ProjectAlertConfig = self._get_project_alert_config(
            project_id, workspace_id, domain_id
        )
        return project_alert_config_vo.options.recovery_mode == "AUTO"

    def _get_project_alert_config(self, project_id, workspace_id, domain_id):
        project_alert_config_mgr: ProjectAlertConfigManager = self.locator.get_manager(
            "ProjectAlertConfigManager"
        )
        return project_alert_config_mgr.get_project_alert_config(
            project_id, workspace_id, domain_id
        )

    def _get_notification_urgency(self, project_id, workspace_id, domain_id):
        project_alert_config_vo: ProjectAlertConfig = self._get_project_alert_config(
            project_id, workspace_id, domain_id
        )
        return project_alert_config_vo.options.notification_urgency

    def _create_notification(self, alert_id, domain_id, method):
        # if alert_vo.state != 'ERROR':
        self._set_transaction_token()

        job_mgr: JobManager = self.locator.get_manager("JobManager")
        job_mgr.push_task(
            "monitoring_alert_notification_from_webhook",
            "JobService",
            method,
            {"alert_id": alert_id, "domain_id": domain_id},
        )

    def _set_transaction_token(self):
        self.transaction.set_meta("token", config.get_global("TOKEN"))

    @staticmethod
    def _create_error_event(webhook_name, error_message):
        response = {
            "results": [
                {
                    "event_key": utils.generate_id("error"),
                    "event_type": "ERROR",
                    "title": f"Webhook Event Parsing Error - {webhook_name}",
                    "description": error_message,
                    "severity": "CRITICAL",
                }
            ]
        }

        return response
