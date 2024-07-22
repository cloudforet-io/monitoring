import logging
from datetime import datetime

from spaceone.core import utils, cache
from spaceone.core.service import *

from spaceone.monitoring.error.alert import *
from spaceone.monitoring.manager.alert_manager import AlertManager
from spaceone.monitoring.manager.event_manager import EventManager
from spaceone.monitoring.manager.job_manager import JobManager
from spaceone.monitoring.manager.identity_manager import IdentityManager
from spaceone.monitoring.manager.project_alert_config_manager import (
    ProjectAlertConfigManager,
)
from spaceone.monitoring.manager.escalation_policy_manager import (
    EscalationPolicyManager,
)
from spaceone.monitoring.manager.config_manager import ConfigManager

from spaceone.monitoring.model.alert_model import Alert
from spaceone.monitoring.model.escalation_policy_model import EscalationPolicy
from spaceone.monitoring.model.project_alert_config_model import ProjectAlertConfig

_LOGGER = logging.getLogger(__name__)


@authentication_handler
@authorization_handler
@mutation_handler
@event_handler
class AlertService(BaseService):
    resource = "Alert"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.alert_mgr: AlertManager = self.locator.get_manager("AlertManager")
        self.event_mgr: EventManager = self.locator.get_manager("EventManager")

    @transaction(
        permission="monitoring:Alert.write",
        role_types=["WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @check_required(["title", "project_id", "domain_id", "workspace_id"])
    def create(self, params: dict) -> Alert:
        """Create alert

        Args:
            params (dict): {
                'title': 'str',           # required
                'description': 'str',
                'assignee': 'str',
                'urgency': 'str',
                'project_id': 'str',      # required
                'domain_id': 'str',       # injected from auth (required)
                'workspace_id': 'str',    # injected from auth (required)
            }

        Returns:
            alert_vo (object)
        """

        project_id = params["project_id"]
        domain_id = params["domain_id"]
        workspace_id = params["workspace_id"]
        assignee = params.get("assignee")

        project_alert_config_mgr: ProjectAlertConfigManager = self.locator.get_manager(
            "ProjectAlertConfigManager"
        )

        project_alert_config_vo: ProjectAlertConfig = (
            project_alert_config_mgr.get_project_alert_config(
                project_id, workspace_id, domain_id
            )
        )
        escalation_policy_vo: EscalationPolicy = (
            project_alert_config_vo.escalation_policy
        )

        params["escalation_policy_id"] = escalation_policy_vo.escalation_policy_id
        params["escalation_ttl"] = escalation_policy_vo.repeat_count + 1
        params["escalated_at"] = None

        if assignee:
            identity_mgr = self.locator.get_manager("IdentityManager")
            identity_mgr.get_workspace_user(user_id=assignee)

        params["triggered_by"] = self.transaction.get_meta("authorization.user_id")

        alert_vo = self.alert_mgr.create_alert(params)

        self._create_notification(alert_vo, "create_alert_notification")

        return alert_vo

    @transaction(
        permission="monitoring:Alert.write",
        role_types=["WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @check_required(["alert_id", "domain_id", "workspace_id"])
    def update(self, params):
        """Update alert

        Args:
            params (dict): {
                'alert_id': 'str',             # required
                'title': 'str',
                'state': 'str',
                'description': 'str',
                'reset_description': 'bool',
                'urgency': 'str',
                'project_id': 'str',           # required
                'domain_id': 'str',            # injected from auth (required)
                'workspace_id': 'str',         # injected from auth (required)
                'user_projects': 'list',       # injected from auth
            }

        Returns:
            alert_vo (object)
        """

        alert_id = params["alert_id"]
        domain_id = params["domain_id"]
        workspace_id = params["workspace_id"]
        user_projects = params.get("user_projects")
        project_id = params.get("project_id")
        state = params.get("state")
        reset_description = params.get("reset_description", False)

        is_resolved_notify = False

        if project_id:
            project_alert_config_mgr: ProjectAlertConfigManager = (
                self.locator.get_manager("ProjectAlertConfigManager")
            )

            project_alert_config_vo: ProjectAlertConfig = (
                project_alert_config_mgr.get_project_alert_config(
                    project_id, workspace_id, domain_id
                )
            )
            escalation_policy_vo: EscalationPolicy = (
                project_alert_config_vo.escalation_policy
            )

            params["escalation_policy_id"] = escalation_policy_vo.escalation_policy_id
            params["escalation_ttl"] = escalation_policy_vo.repeat_count
            params["escalation_step"] = 1
            params["escalated_at"] = None

        if state:
            if state == "ACKNOWLEDGED":
                params["responder"] = self.transaction.get_meta("authorization.user_id")
                params["acknowledged_at"] = datetime.utcnow()
                params["resolved_at"] = None
            elif state == "RESOLVED":
                params["escalation_ttl"] = 0
                params["resolved_at"] = datetime.utcnow()
            elif state == "TRIGGERED":
                params["acknowledged_at"] = None
                params["resolved_at"] = None

        alert_vo = self.alert_mgr.get_alert(
            alert_id, domain_id, workspace_id, user_projects
        )

        if alert_vo.state == "ERROR":
            raise ERROR_INVALID_PARAMETER(
                key="state", reason="The error state cannot be changed."
            )

        if reset_description:
            params["description"] = ""

        if alert_vo.state in ["TRIGGERED", "ACKNOWLEDGED"] and state == "RESOLVED":
            is_resolved_notify = True

        updated_alert_vo: Alert = self.alert_mgr.update_alert_by_vo(params, alert_vo)

        if is_resolved_notify:
            self._create_notification(updated_alert_vo, "create_resolved_notification")

        return updated_alert_vo

    @transaction(
        permission="monitoring:Alert.write",
        role_types=["WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @check_required(["alert_id", "domain_id", "workspace_id"])
    def assign_user(self, params):
        """Assign user to alert

        Args:
            params (dict): {
                'alert_id': 'str',             # required
                'assignee': 'str',             # required
                'domain_id': 'str',            # injected from auth (required)
                'workspace_id': 'str',         # injected from auth (required)
                'user_projects': 'list',       # injected from auth
            }

        Returns:
            alert_vo (object)
        """

        alert_id = params["alert_id"]
        domain_id = params["domain_id"]
        workspace_id = params["workspace_id"]
        user_projects = params.get("user_projects")
        assignee = params["assignee"]

        identity_mgr = self.locator.get_manager("IdentityManager")
        identity_mgr.get_workspace_user(user_id=assignee)

        alert_vo = self.alert_mgr.get_alert(
            alert_id, domain_id, workspace_id, user_projects
        )
        alert_vo = self.alert_mgr.update_alert_by_vo({"assignee": assignee}, alert_vo)
        return alert_vo

    @transaction(exclude=["authentication", "authorization", "mutation"])
    @check_required(["alert_id", "domain_id"])
    def get_alert_info(self, params):
        """Get alert info

        Args:
            params (dict): {
                'alert_id': 'str',          # required
                'domain_id': 'str',         # required
            }

        Returns:
            alert_data (dict)
        """
        alert_id = params["alert_id"]
        domain_id = params["domain_id"]

        alert_vo = self.alert_mgr.get_alert(alert_id, domain_id)

        resources_info = []
        for resource in alert_vo.resources:
            resources_info.append(
                {
                    "resource_id": resource.resource_id,
                    "resource_type": resource.resource_type,
                    "name": resource.name,
                }
            )

        escalation_policy_id = alert_vo.escalation_policy_id
        escalation_policy_name = self._get_escalation_policy_name(
            escalation_policy_id, domain_id
        )

        project_id = alert_vo.project_id
        project_name = self._get_project_name(project_id, domain_id)

        domain_settings = self._get_domain_settings(domain_id)

        return {
            "alert_number": alert_vo.alert_number,
            "alert_id": alert_vo.alert_id,
            "title": alert_vo.title,
            "description": alert_vo.description,
            "state": alert_vo.state,
            "assignee": alert_vo.assignee,
            "responder": alert_vo.responder,
            "urgency": alert_vo.urgency,
            "severity": alert_vo.severity,
            "rule": alert_vo.rule,
            "image_url": alert_vo.image_url,
            "resources": resources_info,
            "provider": alert_vo.provider,
            "account": alert_vo.account,
            "additional_info": alert_vo.additional_info,
            "triggered_by": alert_vo.triggered_by,
            "webhook_id": alert_vo.webhook_id,
            "escalation_policy_id": escalation_policy_id,
            "escalation_policy_name": escalation_policy_name,
            "project_id": project_id,
            "project_name": project_name,
            "workspace_id": alert_vo.workspace_id,
            "domain_id": alert_vo.domain_id,
            "created_at": utils.datetime_to_iso8601(alert_vo.created_at),
            "updated_at": utils.datetime_to_iso8601(alert_vo.updated_at),
            "acknowledged_at": utils.datetime_to_iso8601(alert_vo.acknowledged_at),
            "resolved_at": utils.datetime_to_iso8601(alert_vo.resolved_at),
            "escalated_at": utils.datetime_to_iso8601(alert_vo.escalated_at),
            "domain_settings": domain_settings,
        }

    @cache.cacheable(
        key="monitoring:escalation-policy-name:{domain_id}:{escalation_policy_id}",
        expire=600,
    )
    def _get_escalation_policy_name(
        self, escalation_policy_id: str, domain_id: str
    ) -> str:
        escalation_policy_mgr: EscalationPolicyManager = self.locator.get_manager(
            "EscalationPolicyManager"
        )

        escalation_policy_vos = escalation_policy_mgr.filter_escalation_policies(
            escalation_policy_id=escalation_policy_id,
            domain_id=domain_id,
        )

        if escalation_policy_vos.count() == 0:
            return ""
        else:
            escalation_policy_vo = escalation_policy_vos[0]
            return escalation_policy_vo.name

    @cache.cacheable(key="monitoring:project-name:{domain_id}:{project_id}", expire=600)
    def _get_project_name(self, project_id: str, domain_id: str) -> str:
        try:
            identity_mgr: IdentityManager = self.locator.get_manager(IdentityManager)
            project_info = identity_mgr.get_project_from_system(project_id, domain_id)

            if project_group_id := project_info.get("project_group_id"):
                project_group_info = identity_mgr.get_project_group_from_system(
                    project_group_id, domain_id
                )

                return f'{project_group_info["name"]} > {project_info["name"]}'
            else:
                return project_info["name"]
        except Exception as e:
            _LOGGER.error(
                f"[_get_project_name] Failed to get project: {e}", exc_info=True
            )

            return ""

    @cache.cacheable(key="monitoring:domain-settings:{domain_id}", expire=600)
    def _get_domain_settings(self, domain_id: str) -> dict:
        try:
            config_mgr: ConfigManager = self.locator.get_manager("ConfigManager")
            domain_settings = config_mgr.get_domain_config("settings", domain_id)
            settings_data = domain_settings.get("data", {})
            language = settings_data.get("language", "en")
            timezone = settings_data.get("timezone", "UTC")

            return {
                "language": language,
                "timezone": timezone,
            }

        except Exception as e:
            _LOGGER.error(
                f"[_get_domain_settings] Failed to get domain settings: {e}",
                exc_info=True,
            )

            return {
                "language": "en",
                "timezone": "UTC",
            }

    @transaction(exclude=["authentication", "authorization", "mutation"])
    @check_required(["alert_id", "domain_id"])
    def update_state(self, params):
        """Update alert state

        Args:
            params (dict): {
                'alert_id': 'str',          # required
                'domain_id': 'str',         # required
                'responder': 'str',
            }

        Returns:
            None
        """
        alert_id = params["alert_id"]
        domain_id = params["domain_id"]
        responder = params.get("responder")

        alert_vo = self.alert_mgr.get_alert(alert_id, domain_id)

        if alert_vo.state == "TRIGGERED":
            update_params = {
                "state": "ACKNOWLEDGED",
                "acknowledged_at": datetime.utcnow(),
            }

            if responder:
                update_params["responder"] = responder

            self.alert_mgr.update_alert_by_vo(update_params, alert_vo)

    @transaction(
        permission="monitoring:Alert.write",
        role_types=["WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @check_required(["alert_id", "domain_id", "workspace_id"])
    def delete(self, params):
        """Delete alert

        Args:
            params (dict): {
                'alert_id': 'str',
                'domain_id': 'str',            # injected from auth (required)
                'workspace_id': 'str',         # injected from auth (required)
                'user_projects': 'list',       # injected from auth
            }

        Returns:
            None
        """

        self.alert_mgr.delete_alert(
            params["alert_id"],
            params["domain_id"],
            params["workspace_id"],
            params.get("user_projects"),
        )

    @transaction(
        permission="monitoring:Alert.read",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @check_required(["alert_id", "domain_id"])
    def get(self, params):
        """Get alert

        Args:
            params (dict): {
                'alert_id': 'str',
                'domain_id': 'str',            # injected from auth (required)
                'workspace_id': 'str',         # injected from auth
                'user_projects': 'list',       # injected from auth
            }

        Returns:
            alert_vo (object)
        """

        return self.alert_mgr.get_alert(
            params["alert_id"],
            params["domain_id"],
            params.get("workspace_id"),
            params.get("user_projects"),
        )

    @transaction(
        permission="monitoring:Alert.read",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @check_required(["domain_id"])
    @append_query_filter(
        [
            "alert_number",
            "alert_id",
            "title",
            "state",
            "assignee",
            "urgency",
            "severity",
            "resource",
            "triggered_by",
            "webhook_id",
            "escalation_policy_id",
            "project_id",
            "workspace_id",
            "domain_id",
            "user_projects",
        ]
    )
    @append_keyword_filter(["alert_id", "alert_number_str", "title"])
    def list(self, params):
        """List alerts

        Args:
            params (dict): {
                'query': 'dict (spaceone.api.core.v1.Query)',
                'alert_number': 'str',
                'alert_id': 'str',
                'title': 'str',
                'state': 'str',
                'assignee': 'str',
                'urgency': 'str',
                'severity': 'str',
                'resource': 'str',
                'webhook_id': 'bool',
                'escalation_policy_id': 'str',
                'project_id': 'str',
                'workspace_id': 'str',                          # injected from auth
                'domain_id': 'str',                             # injected from auth (required)
                'user_projects': 'list'                         # injected from auth
            }

        Returns:
            alert_vos (object)
            total_count
        """

        query = params.get("query", {})
        return self.alert_mgr.list_alerts(query)

    @transaction(
        permission="monitoring:Alert.read",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @check_required(["query", "domain_id"])
    @append_query_filter(["workspace_id", "domain_id", "user_projects"])
    @append_keyword_filter(["alert_id", "title"])
    def stat(self, params):
        """
        Args:
            params (dict): {
                'query': 'dict (spaceone.api.core.v1.StatisticsQuery)',
                'domain_id': 'str',            # injected from auth (required)
                'workspace_id': 'str',         # injected from auth
                'user_projects': 'list',       # injected from auth
            }

        Returns:
            values (list) : 'list of statistics data'

        """

        query = params.get("query", {})
        return self.alert_mgr.stat_alerts(query)

    def _create_notification(
        self, alert_vo: Alert, method: str, user_id: str = None
    ) -> None:
        params = {
            "alert_id": alert_vo.alert_id,
            "domain_id": alert_vo.domain_id,
            "workspace_id": alert_vo.workspace_id,
        }

        if user_id:
            params["user_id"] = user_id

        job_mgr: JobManager = self.locator.get_manager("JobManager")
        job_mgr.push_task(
            "monitoring_alert_notification_from_manual", "JobService", method, params
        )

    @staticmethod
    def _check_state(state: str) -> None:
        if state not in ["ACKNOWLEDGED", "RESOLVED"]:
            raise ERROR_INVALID_PARAMETER(
                key="state", reason="Unsupported state. (ACKNOWLEDGED | RESOLVED)"
            )
