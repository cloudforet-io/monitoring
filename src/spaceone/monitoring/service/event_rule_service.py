import fnmatch
import logging
from copy import deepcopy

from spaceone.core.service import *

from spaceone.monitoring.error.event_rule import *
from spaceone.monitoring.manager.event_rule_manager import EventRuleManager
from spaceone.monitoring.manager.identity_manager import IdentityManager
from spaceone.monitoring.manager.escalation_policy_manager import (
    EscalationPolicyManager,
)
from spaceone.monitoring.model.event_rule_model import EventRule

_LOGGER = logging.getLogger(__name__)

_SUPPORTED_CONDITION_KEYS = [
    "title",
    "description",
    "rule",
    "severity",
    "resource",
    "account",
    "webhook_id",
    "project_id",
    "additional_info.<key>",
]
_SUPPORTED_CONDITION_OPERATORS = ["eq", "contain", "not", "not_contain"]


@authentication_handler
@authorization_handler
@mutation_handler
@event_handler
class EventRuleService(BaseService):
    resource = "EventRule"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.event_rule_mgr: EventRuleManager = self.locator.get_manager(
            "EventRuleManager"
        )
        self.escalation_policy_manager: EscalationPolicyManager = (
            self.locator.get_manager("EscalationPolicyManager")
        )

    @transaction(
        permission="monitoring:EventRule.write",
        role_types=["WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @check_required(
        [
            "conditions",
            "conditions_policy",
            "actions",
            "resource_group",
            "domain_id",
            "workspace_id",
        ]
    )
    def create(self, params: dict) -> EventRule:
        """Create event rule

        Args:
            params (dict): {
                'name': 'str',
                'conditions': 'list',          # required
                'conditions_policy': 'str',    # required
                'actions': 'dict',             # required
                'options': 'dict',
                'project_id': 'str',
                'tags': 'dict',
                'resource_group': 'str',       # required
                'domain_id': 'str'             # injected from auth (required)
                'workspace_id': 'str'          # injected from auth (required)
            }

        Returns:
            event_rule_vo (object)
        """

        resource_group = params["resource_group"]
        project_id = params.get("project_id")
        domain_id = params["domain_id"]
        workspace_id = params["workspace_id"]
        project_ids = []

        identity_mgr: IdentityManager = self.locator.get_manager("IdentityManager")

        if resource_group == "PROJECT":
            project_info = identity_mgr.get_project(project_id)
            params["workspace_id"] = project_info.get("workspace_id")
            workspace_id = params["workspace_id"]
            project_ids.append(project_info.get("project_id"))
        else:
            identity_mgr.check_workspace(workspace_id, domain_id)
            params["project_id"] = "*"
            project_id = params["project_id"]

        self._check_conditions(params["conditions"])
        self._check_actions(params["actions"], domain_id, workspace_id, identity_mgr)

        self._check_recursive_actions(
            identity_mgr, params["actions"], domain_id, workspace_id, project_ids
        )

        params["order"] = (
            self._get_highest_order(resource_group, project_id, domain_id, workspace_id)
            + 1
        )

        return self.event_rule_mgr.create_event_rule(params)

    @transaction(
        permission="monitoring:EventRule.write",
        role_types=["WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @check_required(["event_rule_id", "domain_id", "workspace_id"])
    def update(self, params: dict) -> EventRule:
        """Update event rule

        Args:
            params (dict): {
                'event_rule_id': 'dict',        # required
                'name': 'str',
                'conditions': 'list',
                'conditions_policy': 'str',
                'actions': 'dict',
                'options': 'dict',
                'tags': 'dict',
                'domain_id': 'str',             # injected from auth (required)
                'workspace_id': 'str',          # injected from auth (required)
                'user_projects': 'list'         # injected from auth
            }

        Returns:
            event_rule_vo (object)
        """

        event_rule_id = params["event_rule_id"]
        domain_id = params["domain_id"]
        workspace_id = params["workspace_id"]
        user_projects = params.get("user_projects")
        project_ids = []

        event_rule_vo = self.event_rule_mgr.get_event_rule(
            event_rule_id, domain_id, workspace_id, user_projects
        )

        if event_rule_vo.resource_group == "PROJECT":
            project_ids.append(event_rule_vo.project_id)

        if "conditions" in params:
            self._check_conditions(params["conditions"])

        actions = params.get("actions") or event_rule_vo.actions
        if actions:
            identity_mgr: IdentityManager = self.locator.get_manager("IdentityManager")
            self._check_actions(
                actions,
                domain_id,
                workspace_id,
                identity_mgr,
            )

            self._check_recursive_actions(
                identity_mgr, actions, domain_id, workspace_id, project_ids
            )

        return self.event_rule_mgr.update_event_rule_by_vo(params, event_rule_vo)

    @transaction(
        permission="monitoring:EventRule.write",
        role_types=["WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @check_required(["event_rule_id", "order", "domain_id", "workspace_id"])
    def change_order(self, params: dict) -> EventRule:
        """Get event rule

        Args:
            params (dict): {
                'event_rule_id': 'str',     # required
                'order': 'int',             # required
                'domain_id': 'str',         # injected from auth (required)
                'workspace_id': 'str',      # injected from auth (required)
                'user_projects': 'list'     # injected from auth
            }

        Returns:
            event_rule_vo (object)
        """

        event_rule_id = params["event_rule_id"]
        order = params["order"]
        domain_id = params["domain_id"]
        workspace_id = params["workspace_id"]
        user_projects = params.get("user_projects")

        self._check_order(order)

        target_event_rule_vo = self.event_rule_mgr.get_event_rule(
            event_rule_id, domain_id, workspace_id, user_projects
        )

        if target_event_rule_vo.order == order:
            return target_event_rule_vo

        highest_order = self._get_highest_order(
            target_event_rule_vo.resource_group,
            target_event_rule_vo.project_id,
            target_event_rule_vo.domain_id,
            target_event_rule_vo.workspace_id,
        )

        if order > highest_order:
            raise ERROR_INVALID_PARAMETER(
                key="order",
                reason=f"There is no event rules greater than the {str(order)} order.",
            )

        event_rule_vos = self._get_all_event_rules(
            target_event_rule_vo.resource_group,
            target_event_rule_vo.project_id,
            domain_id,
            workspace_id,
            target_event_rule_vo.event_rule_id,
        )
        event_rule_vos.insert(order - 1, target_event_rule_vo)

        for idx, event_rule_vo in enumerate(event_rule_vos):
            if target_event_rule_vo != event_rule_vo:
                self.event_rule_mgr.update_event_rule_by_vo(
                    {"order": idx + 1}, event_rule_vo
                )

        return self.event_rule_mgr.update_event_rule_by_vo(
            {"order": order}, target_event_rule_vo
        )

    @transaction(
        permission="monitoring:EventRule.write",
        role_types=["WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @check_required(["event_rule_id", "domain_id", "workspace_id"])
    def delete(self, params):
        """Delete event rule

        Args:
            params (dict): {
                'event_rule_id': 'str',     # required
                'domain_id': 'str',         # injected from auth (required)
                'workspace_id': 'str',      # injected from auth (required)
                'user_projects': 'list'     # injected from auth
            }

        Returns:
            None
        """

        event_rule_id = params["event_rule_id"]
        domain_id = params["domain_id"]
        workspace_id = params["workspace_id"]
        user_projects = params.get("user_projects")

        event_rule_vo: EventRule = self.event_rule_mgr.get_event_rule(
            event_rule_id, domain_id, workspace_id, user_projects
        )

        resource_group = event_rule_vo.resource_group
        project_id = event_rule_vo.project_id

        self.event_rule_mgr.delete_event_rule_by_vo(event_rule_vo)

        event_rule_vos = self._get_all_event_rules(
            resource_group, project_id, domain_id, workspace_id
        )

        i = 0
        for event_rule_vo in event_rule_vos:
            self.event_rule_mgr.update_event_rule_by_vo({"order": i + 1}, event_rule_vo)
            i += 1

    @transaction(
        permission="monitoring:EventRule.read",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @change_value_by_rule("APPEND", "workspace_id", "*")
    @change_value_by_rule("APPEND", "project_id", "*")
    @change_value_by_rule("APPEND", "user_projects", "*")
    @check_required(["event_rule_id", "domain_id"])
    def get(self, params):
        """Get event rule

        Args:
            params (dict): {
                'event_rule_id': 'str',     # required
                'domain_id': 'str',         # injected from auth (required)
                'workspace_id': 'str',      # injected from auth
                'user_projects': 'list'     # injected from auth
            }

        Returns:
            event_rule_vo (object)
        """

        return self.event_rule_mgr.get_event_rule(
            params["event_rule_id"],
            params["domain_id"],
            params["workspace_id"],
            params.get("user_projects"),
        )

    @transaction(
        permission="monitoring:EventRule.read",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @change_value_by_rule("APPEND", "workspace_id", "*")
    @change_value_by_rule("APPEND", "project_id", "*")
    @change_value_by_rule("APPEND", "user_projects", "*")
    @check_required(["domain_id"])
    @append_query_filter(
        [
            "event_rule_id",
            "name",
            "resource_group",
            "project_id",
            "workspace_id",
            "domain_id",
            "user_projects",
        ]
    )
    @append_keyword_filter(["event_rule_id", "name"])
    def list(self, params):
        """List escalation polices

        Args:
            params (dict): {
                'query': 'dict (spaceone.api.core.v1.Query)',
                'event_rule_id': 'str',
                'name': 'str',
                'resource_group': 'str',
                'project_id': 'str',
                'workspace_id': 'str',
                'domain_id': 'str',         # injected from auth (required)
                'user_projects': 'list'     # injected from auth
            }

        Returns:
            event_rule_vos (object)
            total_count
        """

        query = params.get("query", {})
        return self.event_rule_mgr.list_event_rules(query)

    @transaction(
        permission="monitoring:EventRule.read",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @change_value_by_rule("APPEND", "workspace_id", "*")
    @change_value_by_rule("APPEND", "project_id", "*")
    @change_value_by_rule("APPEND", "user_projects", "*")
    @check_required(["query", "domain_id"])
    @append_query_filter(["domain_id", "workspace_id", "user_projects"])
    @append_keyword_filter(["event_rule_id", "name"])
    def stat(self, params):
        """
        Args:
            params (dict): {
                'query': 'dict (spaceone.api.core.v1.StatisticsQuery)',
                'domain_id': 'str',         # injected from auth (required)
                'workspace_id': 'str',      # injected from auth
                'user_projects': 'list'     # injected from auth
            }

        Returns:
            values (list) : 'list of statistics data'

        """

        query = params.get("query", {})
        return self.event_rule_mgr.stat_event_rules(query)

    @staticmethod
    def _check_conditions(conditions: list) -> None:
        for condition in conditions:
            key = condition.get("key")
            value = condition.get("value")
            operator = condition.get("operator")

            if not (key and value and operator):
                raise ERROR_INVALID_PARAMETER(
                    key="conditions",
                    reason="Condition should have key, value and operator.",
                )

            if key not in _SUPPORTED_CONDITION_KEYS and not fnmatch.fnmatch(
                key, "additional_info.*"
            ):
                raise ERROR_INVALID_PARAMETER(
                    key="conditions.key",
                    reason=f"Unsupported key. "
                    f'({" | ".join(_SUPPORTED_CONDITION_KEYS)})',
                )
            if operator not in _SUPPORTED_CONDITION_OPERATORS:
                raise ERROR_INVALID_PARAMETER(
                    key="conditions.operator",
                    reason=f"Unsupported operator. "
                    f'({" | ".join(_SUPPORTED_CONDITION_OPERATORS)})',
                )

    def _check_actions(
        self,
        actions: dict,
        domain_id: str,
        workspace_id: str,
        identity_mgr: IdentityManager,
    ) -> None:
        if change_project_id := actions.get("change_project"):
            identity_mgr.get_project(change_project_id, domain_id)
        elif change_urgency := actions.get("change_urgency"):
            if change_urgency not in ["HIGH", "LOW"]:
                raise ERROR_INVALID_PARAMETER(
                    key="actions.change_urgency",
                    reason=f"Unsupported urgency. (HIGH | LOW)",
                )
        elif change_assignee := actions.get("change_assignee"):
            if not isinstance(change_assignee, str):
                raise ERROR_INVALID_PARAMETER_TYPE(
                    key="actions.change_assignee", type="str"
                )
        elif change_escalation_policy_id := actions.get("change_escalation_policy"):
            self.escalation_policy_manager.get_escalation_policy(
                change_escalation_policy_id, workspace_id, domain_id
            )
        elif add_additional_info := actions.get("add_additional_info"):
            if not isinstance(add_additional_info, dict):
                raise ERROR_INVALID_PARAMETER_TYPE(
                    key="actions.add_additional_info", type="dict"
                )
        elif no_notification := actions.get("no_notification"):
            if not isinstance(no_notification, bool):
                raise ERROR_INVALID_PARAMETER_TYPE(
                    key="actions.no_notification", type="bool"
                )

    def _check_recursive_actions(
        self,
        identity_mgr: IdentityManager,
        actions: dict,
        domain_id: str,
        workspace_id: str,
        project_ids: list,
    ) -> None:
        visited_project_ids = deepcopy(project_ids)

        change_project_id = actions.get("change_project")
        if not change_project_id:
            return

        if change_project_id in visited_project_ids:
            _LOGGER.error(
                f"[_check_recursive_actions] change_project_id {change_project_id}, project ids: {project_ids} "
            )
            raise ERROR_INVALID_PARAMETER(
                key="actions.change_project",
                reason=f"To avoid an infinite loop, the change_project_id({change_project_id}) in the action must differ from the project_id in the event rule.",
            )

        visited_project_ids.append(change_project_id)
        event_rule_vos = self.event_rule_mgr.filter_event_rules(
            domain_id=domain_id,
            workspace_id=workspace_id,
            project_id=change_project_id,
        )
        for event_rule_vo in event_rule_vos:
            self._check_recursive_actions(
                identity_mgr,
                event_rule_vo.actions,
                domain_id,
                workspace_id,
                visited_project_ids,
            )

    @staticmethod
    def _check_order(order: int) -> None:
        if order <= 0:
            raise ERROR_INVALID_PARAMETER(
                key="order", reason="The order must be greater than 0."
            )

    def _get_highest_order(
        self, resource_group: str, project_id: str, domain_id: str, workspace_id: str
    ) -> int:
        query = {
            "filter": [
                {"k": "domain_id", "v": domain_id, "o": "eq"},
                {"k": "resource_group", "v": resource_group, "o": "eq"},
                {"k": "project_id", "v": project_id, "o": "eq"},
                {"k": "workspace_id", "v": workspace_id, "o": "eq"},
            ],
            "count_only": True,
        }

        event_rule_vos, total_count = self.event_rule_mgr.list_event_rules(query)
        return total_count

    def _get_all_event_rules(
        self,
        resource_group: str,
        project_id: str,
        domain_id: str,
        workspace_id: str,
        exclude_event_rule_id: str = None,
    ):
        query = {
            "filter": [
                {"k": "domain_id", "v": domain_id, "o": "eq"},
                {"k": "workspace_id", "v": workspace_id, "o": "eq"},
                {"k": "resource_group", "v": resource_group, "o": "eq"},
                {"k": "project_id", "v": project_id, "o": "eq"},
            ],
            "sort": [{"key": "order"}],
        }
        if exclude_event_rule_id is not None:
            query["filter"].append(
                {"k": "event_rule_id", "v": exclude_event_rule_id, "o": "not"}
            )

        event_rule_vos, total_count = self.event_rule_mgr.list_event_rules(query)
        return list(event_rule_vos)
