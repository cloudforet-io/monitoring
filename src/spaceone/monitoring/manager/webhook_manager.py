import logging

from spaceone.core import cache
from spaceone.core.manager import BaseManager

from spaceone.monitoring.model.webhook_model import Webhook

_LOGGER = logging.getLogger(__name__)


class WebhookManager(BaseManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.webhook_model: Webhook = self.locator.get_model("Webhook")

    def create_webhook(self, params: dict) -> Webhook:
        def _rollback(vo: Webhook):
            _LOGGER.info(
                f"[create_webhook._rollback] "
                f"Delete webhook : {vo.name} "
                f"({vo.webhook_id})"
            )
            vo.delete()

        webhook_vo: Webhook = self.webhook_model.create(params)
        self.transaction.add_rollback(_rollback, webhook_vo)

        return webhook_vo

    def update_webhook(self, params):
        webhook_vo: Webhook = self.get_webhook(
            params["webhook_id"],
            params["domain_id"],
            params["workspace_id"],
            params.get("user_projects"),
        )
        return self.update_webhook_by_vo(params, webhook_vo)

    def update_webhook_by_vo(self, params: dict, webhook_vo: Webhook) -> Webhook:
        def _rollback(old_data: dict):
            _LOGGER.info(
                f"[update_webhook_by_vo._rollback] Revert Data : "
                f'{old_data["webhook_id"]}'
            )
            webhook_vo.update(old_data)

        self.transaction.add_rollback(_rollback, webhook_vo.to_dict())

        updated_vo: Webhook = webhook_vo.update(params)

        cache.delete(f"webhook-data:{updated_vo.webhook_id}")

        return updated_vo

    def delete_webhook(
        self,
        webhook_id: str,
        domain_id: str,
        workspace_id: str,
        user_projects: list = None,
    ):
        webhook_vo: Webhook = self.get_webhook(
            webhook_id, domain_id, workspace_id, user_projects
        )

        cache.delete(f"webhook-data:{webhook_vo.webhook_id}")

        webhook_vo.delete()

    def get_webhook(
        self,
        webhook_id: str,
        domain_id: str,
        workspace_id: str = None,
        user_projects: list = None,
    ) -> Webhook:
        conditions = {"webhook_id": webhook_id, "domain_id": domain_id}

        if workspace_id:
            conditions["workspace_id"] = workspace_id

        if user_projects:
            conditions["project_id"] = user_projects

        return self.webhook_model.get(**conditions)

    def get_webhook_by_id(self, webhook_id):
        return self.webhook_model.get(webhook_id=webhook_id)

    def list_webhooks(self, query: dict) -> dict:
        return self.webhook_model.query(**query)

    def stat_webhooks(self, query: dict) -> dict:
        return self.webhook_model.stat(**query)
