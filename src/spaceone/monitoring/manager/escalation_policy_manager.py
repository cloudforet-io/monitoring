import copy
import logging

from spaceone.core.manager import BaseManager

from spaceone.monitoring.conf.default_escalation_policy import DEFAULT_ESCALATION_POLICY
from spaceone.monitoring.error.escalation_policy import *
from spaceone.monitoring.model.escalation_policy_model import EscalationPolicy

_LOGGER = logging.getLogger(__name__)


class EscalationPolicyManager(BaseManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.escalation_policy_model: EscalationPolicy = self.locator.get_model(
            "EscalationPolicy"
        )

    def create_escalation_policy(self, params):
        def _rollback(vo: EscalationPolicy):
            _LOGGER.info(
                f"[create_escalation_policy._rollback] "
                f"Delete escalation policy : {vo.name} "
                f"({vo.escalation_policy_id})"
            )
            vo.delete()

        escalation_policy_vo: EscalationPolicy = self.escalation_policy_model.create(
            params
        )
        self.transaction.add_rollback(_rollback, escalation_policy_vo)

        return escalation_policy_vo

    def create_default_escalation_policy(self, domain_id, workspace_id):
        default_escalation_policy = copy.deepcopy(DEFAULT_ESCALATION_POLICY)
        default_escalation_policy["resource_group"] = "WORKSPACE"
        default_escalation_policy["domain_id"] = domain_id
        default_escalation_policy["workspace_id"] = workspace_id
        default_escalation_policy["project_id"] = "*"

        if isinstance(workspace_id, list):
            default_escalation_policy["workspace_id"] = workspace_id[0]

        return self.create_escalation_policy(default_escalation_policy)

    def update_escalation_policy_by_vo(
        self, params: dict, escalation_policy_vo: EscalationPolicy
    ) -> EscalationPolicy:
        def _rollback(old_data: dict):
            _LOGGER.info(
                f"[update_escalation_policy_by_vo._rollback] Revert Data : "
                f'{old_data["escalation_policy_id"]}'
            )
            escalation_policy_vo.update(old_data)

        self.transaction.add_rollback(_rollback, escalation_policy_vo.to_dict())

        updated_vo: EscalationPolicy = escalation_policy_vo.update(params)

        return updated_vo

    def set_default_escalation_policy(self, params, escalation_policy_vo):
        global_escalation_policy_vos = self.escalation_policy_model.filter(
            domain_id=params["domain_id"],
            workspace_id=params["workspace_id"],
            resource_group="WORKSPACE",
        )

        for global_escalation_policy_vo in global_escalation_policy_vos:
            global_escalation_policy_vo.update({"is_default": False})

        return escalation_policy_vo.update({"is_default": True})

    def is_default_escalation_policy(self, domain_id, workspace_id):
        if isinstance(workspace_id, list):
            workspace_id = workspace_id[0]

        query = {
            "count_only": True,
            "filter": [
                {"k": "domain_id", "v": domain_id, "o": "eq"},
                {"k": "workspace_id", "v": workspace_id, "o": "eq"},
            ],
        }

        (
            escalation_policy_vos,
            total_count,
        ) = self.list_escalation_policies(query)

        if total_count == 0:
            return False
        return True

    def get_default_escalation_policy(
        self, workspace_id: str, domain_id: str
    ) -> EscalationPolicy:
        if not self.is_default_escalation_policy(domain_id, workspace_id):
            return self.create_default_escalation_policy(domain_id, workspace_id)
        else:
            query = {
                "domain_id": domain_id,
                "workspace_id": workspace_id,
                "is_default": True,
            }

            return self.escalation_policy_model.get(**query)

    def delete_escalation_policy(
        self,
        escalation_policy_id: str,
        workspace_id: str,
        domain_id: str,
        user_projects: list = None,
    ) -> None:
        conditions = {
            "escalation_policy_id": escalation_policy_id,
            "workspace_id": workspace_id,
            "domain_id": domain_id,
        }

        if user_projects:
            conditions["project_id"] = user_projects

        escalation_policy_vo: EscalationPolicy = self.get_escalation_policy(
            **conditions
        )

        if escalation_policy_vo.is_default:
            raise ERROR_DEFAULT_ESCALATION_POLICY_NOT_ALLOW_DELETION(
                escalation_policy_id=escalation_policy_id
            )

        escalation_policy_vo.delete()

    def get_escalation_policy(
        self,
        escalation_policy_id: str,
        workspace_id: str,
        domain_id: str,
        user_projects: list = None,
    ) -> EscalationPolicy:
        conditions = {
            "escalation_policy_id": escalation_policy_id,
            "workspace_id": workspace_id,
            "domain_id": domain_id,
        }

        if user_projects:
            conditions["project_id"] = user_projects

        return self.escalation_policy_model.get(**conditions)

    def list_escalation_policies(self, query: dict) -> dict:
        return self.escalation_policy_model.query(**query)

    def stat_escalation_policies(self, query: dict) -> dict:
        return self.escalation_policy_model.stat(**query)
