import logging

from spaceone.core.service import *

from spaceone.monitoring.error.escalation_policy import *
from spaceone.monitoring.manager.escalation_policy_manager import (
    EscalationPolicyManager,
)
from spaceone.monitoring.manager.identity_manager import IdentityManager
from spaceone.monitoring.model.escalation_policy_model import EscalationPolicy

_LOGGER = logging.getLogger(__name__)


@authentication_handler
@authorization_handler
@mutation_handler
@event_handler
class EscalationPolicyService(BaseService):
    resource = "EscalationPolicy"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.escalation_policy_mgr: EscalationPolicyManager = self.locator.get_manager(
            "EscalationPolicyManager"
        )

    @transaction(
        permission="monitoring:EscalationPolicy.write",
        role_types=["WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @check_required(["name", "rules", "domain_id", "workspace_id"])
    def create(self, params: dict) -> EscalationPolicy:
        """Create escalation policy

        Args:
            params (dict): {
                'name': 'str',              # required
                'rules': 'list',            # required
                'repeat_count': 'int',
                'finish_condition': 'str',
                'project_id': 'str',
                'tags': 'dict',
                'resource_group': 'str',    # required
                'domain_id': 'str',         # injected from auth (required)
                'workspace_id': 'str',      # injected from auth (required)
            }

        Returns:
            escalation_policy_vo (object)
        """
        resource_group = params["resource_group"]
        project_id = params.get("project_id")
        domain_id = params["domain_id"]
        workspace_id = params["workspace_id"]

        identity_mgr: IdentityManager = self.locator.get_manager("IdentityManager")

        if resource_group == "PROJECT":
            project_info = identity_mgr.get_project(project_id)
            params["workspace_id"] = project_info.get("workspace_id")
        else:
            identity_mgr.check_workspace(workspace_id, domain_id)
            params["project_id"] = "*"

        return self.escalation_policy_mgr.create_escalation_policy(params)

    @transaction(
        permission="monitoring:EscalationPolicy.write",
        role_types=["WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @check_required(["escalation_policy_id", "domain_id", "workspace_id"])
    def update(self, params):
        """Update escalation policy

        Args:
            params (dict): {
                'escalation_policy_id': 'dict',     # required
                'name': 'str',
                'rules': 'list',
                'repeat_count': 'int',
                'finish_condition': 'str',
                'tags': 'dict',
                'domain_id': 'str',                 # injected from auth (required)
                'workspace_id': 'str',              # injected from auth (required)
                'user_projects': 'list'             # injected from auth
            }

        Returns:
            escalation_policy_vo (object)
        """

        escalation_policy_id = params["escalation_policy_id"]
        domain_id = params["domain_id"]
        workspace_id = params["workspace_id"]
        user_projects = params.get("user_projects")

        if "rules" in params:
            params["repeat_count"] = params.get("repeat_count", 0)

        escalation_policy_vo = self.escalation_policy_mgr.get_escalation_policy(
            escalation_policy_id, workspace_id, domain_id, user_projects
        )
        return self.escalation_policy_mgr.update_escalation_policy_by_vo(
            params, escalation_policy_vo
        )

    @transaction(
        permission="monitoring:EscalationPolicy.write",
        role_types=["WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @check_required(["escalation_policy_id", "domain_id", "workspace_id"])
    def set_default(self, params):
        """Get escalation policy

        Args:
            params (dict): {
                'escalation_policy_id': 'str',  # required
                'domain_id': 'str',             # injected from auth (required)
                'workspace_id': 'str',          # injected from auth (required)
                'user_projects': 'list'         # injected from auth
            }

        Returns:
            escalation_policy_vo (object)
        """

        escalation_policy_id = params["escalation_policy_id"]
        domain_id = params["domain_id"]
        workspace_id = params["workspace_id"]
        user_projects = params.get("user_projects")

        escalation_policy_vo: EscalationPolicy = (
            self.escalation_policy_mgr.get_escalation_policy(
                escalation_policy_id, workspace_id, domain_id, user_projects
            )
        )

        if escalation_policy_vo.resource_group != "WORKSPACE":
            raise ERROR_INVALID_ESCALATION_POLICY_SCOPE(
                escalation_policy_id=escalation_policy_id
            )

        if escalation_policy_vo.is_default:
            return escalation_policy_vo
        else:
            return self.escalation_policy_mgr.set_default_escalation_policy(
                params, escalation_policy_vo
            )

    @transaction(
        permission="monitoring:EscalationPolicy.write",
        role_types=["WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @check_required(["escalation_policy_id", "domain_id", "workspace_id"])
    def delete(self, params):
        """Delete escalation policy

        Args:
            params (dict): {
                'escalation_policy_id': 'str',  # required
                'domain_id': 'str',             # injected from auth (required)
                'workspace_id': 'str',          # injected from auth (required)
                'user_projects': 'list'         # injected from auth
            }

        Returns:
            None
        """

        self.escalation_policy_mgr.delete_escalation_policy(
            params["escalation_policy_id"],
            params["workspace_id"],
            params["domain_id"],
            params.get("user_projects"),
        )

    @transaction(
        permission="monitoring:EscalationPolicy.read",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @change_value_by_rule("APPEND", "workspace_id", "*")
    @change_value_by_rule("APPEND", "project_id", "*")
    @change_value_by_rule("APPEND", "user_projects", "*")
    @check_required(["escalation_policy_id", "domain_id", "workspace_id"])
    def get(self, params):
        """Get escalation policy

        Args:
            params (dict): {
                'escalation_policy_id': 'str',  # required
                'domain_id': 'str',             # injected from auth (required)
                'workspace_id': 'str',          # injected from auth
                'user_projects': 'list'         # injected from auth
            }

        Returns:
            escalation_policy_vo (object)
        """

        return self.escalation_policy_mgr.get_escalation_policy(
            params["escalation_policy_id"],
            params["workspace_id"],
            params["domain_id"],
            params.get("user_projects"),
        )

    @transaction(
        permission="monitoring:EscalationPolicy.read",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @change_value_by_rule("APPEND", "workspace_id", "*")
    @change_value_by_rule("APPEND", "project_id", "*")
    @change_value_by_rule("APPEND", "user_projects", "*")
    @check_required(["domain_id"])
    @append_query_filter(
        [
            "escalation_policy_id",
            "name",
            "is_default",
            "finish_condition",
            "resource_group",
            "project_id",
            "domain_id",
            "workspace_id",
            "user_projects",
        ]
    )
    @append_keyword_filter(["escalation_policy_id", "name"])
    def list(self, params):
        """List escalation polices

        Args:
            params (dict): {
                'query': 'dict (spaceone.api.core.v1.Query)',
                'escalation_policy_id': 'str',
                'name': 'str',
                'is_default': 'bool',
                'finish_condition': 'str',
                'resource_group': 'str',
                'project_id': 'str',
                'domain_id': 'str',                            # injected from auth (required)
                'workspace_id': 'str',                         # injected from auth
                'user_projects': 'list'                        # injected from auth
            }

        Returns:
            escalation_policy_vos (object)
            total_count
        """
        domain_id = params["domain_id"]
        workspace_id = params["workspace_id"]

        if not self.escalation_policy_mgr.is_default_escalation_policy(
            domain_id, workspace_id
        ):
            self.escalation_policy_mgr.create_default_escalation_policy(
                domain_id, workspace_id
            )
        query = params.get("query", {})
        return self.escalation_policy_mgr.list_escalation_policies(query)

    @transaction(
        permission="monitoring:EscalationPolicy.read",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @change_value_by_rule("APPEND", "workspace_id", "*")
    @change_value_by_rule("APPEND", "project_id", "*")
    @change_value_by_rule("APPEND", "user_projects", "*")
    @check_required(["query", "workspace_id", "domain_id"])
    @append_query_filter(["domain_id", "workspace_id", "user_projects"])
    @append_keyword_filter(["escalation_policy_id", "name"])
    def stat(self, params):
        """
        Args:
            params (dict): {
                'query': 'dict (spaceone.api.core.v1.StatisticsQuery)',   # required
                'domain_id': 'str',                                       # injected from auth (required)
                'workspace_id': 'str',                                    # injected from auth
                'user_projects': 'list'                                   # injected from auth
            }

        Returns:
            values (list) : 'list of statistics data'

        """

        query = params.get("query", {})
        return self.escalation_policy_mgr.stat_escalation_policies(query)
