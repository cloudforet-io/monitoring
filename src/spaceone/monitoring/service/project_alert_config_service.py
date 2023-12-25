import logging

from spaceone.core.service import *

from spaceone.monitoring.error import *
from spaceone.monitoring.manager.escalation_policy_manager import (
    EscalationPolicyManager,
)
from spaceone.monitoring.manager.identity_manager import IdentityManager
from spaceone.monitoring.manager.project_alert_config_manager import (
    ProjectAlertConfigManager,
)
from spaceone.monitoring.model.project_alert_config_model import ProjectAlertConfig

_LOGGER = logging.getLogger(__name__)


@authentication_handler
@authorization_handler
@mutation_handler
@event_handler
class ProjectAlertConfigService(BaseService):
    resource = "ProjectAlertConfig"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.project_alert_config_mgr: ProjectAlertConfigManager = (
            self.locator.get_manager("ProjectAlertConfigManager")
        )

    @transaction(
        permission="monitoring:ProjectAlertConfig.write",
        role_types=["WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @check_required(["project_id", "domain_id", "workspace_id"])
    def create(self, params: dict) -> ProjectAlertConfig:
        """Create project alert configuration

        Args:
            params (dict): {
                'project_id': 'str',            # required
                'escalation_policy_id': 'str',
                'options': 'dict',
                'domain_id': 'str'              # injected from auth (required)
                'workspace_id': 'str',          # injected from auth (required)
            }

        Returns:
            project_alert_config_vo (object)
        """

        project_id = params["project_id"]
        escalation_policy_id = params.get("escalation_policy_id")
        domain_id = params["domain_id"]
        workspace_id = params["workspace_id"]

        identity_mgr: IdentityManager = self.locator.get_manager("IdentityManager")
        escalation_policy_mgr: EscalationPolicyManager = self.locator.get_manager(
            "EscalationPolicyManager"
        )

        identity_mgr.get_project(project_id)

        if escalation_policy_id:
            escalation_policy_vo = escalation_policy_mgr.get_escalation_policy(
                escalation_policy_id, workspace_id, domain_id
            )
            if (
                escalation_policy_vo.resource_group == "PROJECT"
                and escalation_policy_vo.project_id != project_id
            ):
                raise ERROR_INVALID_ESCALATION_POLICY(
                    escalation_policy_id=escalation_policy_id
                )

            params["escalation_policy"] = escalation_policy_vo

        else:
            escalation_policy_vo = escalation_policy_mgr.get_default_escalation_policy(
                workspace_id, domain_id
            )
            params["escalation_policy_id"] = escalation_policy_vo.escalation_policy_id
            params["escalation_policy"] = escalation_policy_vo

        return self.project_alert_config_mgr.create_project_alert_config(params)

    @transaction(
        permission="monitoring:ProjectAlertConfig.write",
        role_types=["WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @check_required(["project_id", "domain_id", "workspace_id"])
    def update(self, params):
        """Update project alert configuration

        Args:
            params (dict): {
                'project_id': 'str',             # required
                'escalation_policy_id': 'dict',
                'options': 'dict',
                'domain_id': 'str'               # injected from auth (required)
                'workspace_id': 'str',           # injected from auth (required)
            }

        Returns:
            project_alert_config_vo (object)
        """

        project_id = params["project_id"]
        escalation_policy_id = params.get("escalation_policy_id")
        domain_id = params["domain_id"]
        workspace_id = params["workspace_id"]

        project_alert_config_vo: ProjectAlertConfig = (
            self.project_alert_config_mgr.get_project_alert_config(
                project_id, workspace_id, domain_id
            )
        )

        if escalation_policy_id:
            escalation_policy_mgr: EscalationPolicyManager = self.locator.get_manager(
                "EscalationPolicyManager"
            )
            escalation_policy_vo = escalation_policy_mgr.get_escalation_policy(
                escalation_policy_id=escalation_policy_id,
                workspace_id=workspace_id,
                domain_id=domain_id,
            )
            if (
                escalation_policy_vo.resource_group == "PROJECT"
                and escalation_policy_vo.project_id != project_id
            ):
                raise ERROR_INVALID_ESCALATION_POLICY(
                    escalation_policy_id=escalation_policy_id
                )

            params["escalation_policy"] = escalation_policy_vo

        if "options" in params:
            if "recovery_mode" not in params["options"]:
                params["options"][
                    "recovery_mode"
                ] = project_alert_config_vo.options.recovery_mode

            if "notification_urgency" not in params["options"]:
                params["options"][
                    "notification_urgency"
                ] = project_alert_config_vo.options.notification_urgency

        return self.project_alert_config_mgr.update_project_alert_config_by_vo(
            params, project_alert_config_vo
        )

    @transaction(
        permission="monitoring:ProjectAlertConfig.write",
        role_types=["WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @check_required(["project_id", "domain_id", "workspace_id"])
    def delete(self, params):
        """Delete project alert configuration

        Args:
            params (dict): {
                'project_id': 'str',       # required
                'domain_id': 'str'         # injected from auth (required)
                'workspace_id': 'str',     # injected from auth (required)
            }

        Returns:
            None
        """

        self.project_alert_config_mgr.delete_project_alert_config(
            params["project_id"], params["domain_id"], params["workspace_id"]
        )

    @transaction(
        permission="monitoring:ProjectAlertConfig.read",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @check_required(["project_id", "domain_id", "workspace_id"])
    @change_only_key({"escalation_policy_info": "escalation_policy"})
    def get(self, params):
        """Get project alert configuration

        Args:
            params (dict): {
                'project_id': 'str',       # required
                'domain_id': 'str'         # injected from auth (required)
                'workspace_id': 'str',     # injected from auth (required)
            }

        Returns:
            project_alert_config_vo (object)
        """

        return self.project_alert_config_mgr.get_project_alert_config(
            params["project_id"], params["workspace_id"], params["domain_id"]
        )

    @transaction(
        permission="monitoring:ProjectAlertConfig.read",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @check_required(["domain_id", "workspace_id"])
    @change_only_key(
        {"escalation_policy_info": "escalation_policy"}, key_path="query.only"
    )
    @append_query_filter(
        [
            "project_id",
            "escalation_policy_id",
            "domain_id",
            "workspace_id",
            "user_projects",
        ]
    )
    @append_keyword_filter(["project_id"])
    def list(self, params):
        """List project alert configurations

        Args:
            params (dict): {
                'query': 'dict (spaceone.api.core.v1.Query)',
                'project_id': 'str',
                'escalation_policy_id': 'str',
                'domain_id': 'str'         # injected from auth (required)
                'workspace_id': 'str',     # injected from auth (required)
                'user_projects': 'list'    # injected from auth (required)
            }

        Returns:
            project_alert_config_vos (object)
            total_count
        """

        query = params.get("query", {})
        return self.project_alert_config_mgr.list_project_alert_configs(query)

    @transaction(
        permission="monitoring:ProjectAlertConfig.read",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @check_required(["query", "domain_id"])
    @append_query_filter(["domain_id", "workspace_id", "user_projects"])
    @append_keyword_filter(["project_id"])
    def stat(self, params):
        """
        Args:
            params (dict): {
                'query': 'dict (spaceone.api.core.v1.StatisticsQuery)',
                'domain_id': 'str'         # injected from auth (required)
                'workspace_id': 'str',     # injected from auth (required)
                'user_projects': 'list'    # injected from auth (required)
            }

        Returns:
            values (list) : 'list of statistics data'

        """

        query = params.get("query", {})
        return self.project_alert_config_mgr.stat_project_alert_configs(query)
