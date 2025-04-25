import logging

from spaceone.core.manager import BaseManager

from spaceone.monitoring.model.alert_model import Alert, AlertNumber

_LOGGER = logging.getLogger(__name__)


class AlertManager(BaseManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.alert_model: Alert = self.locator.get_model("Alert")
        self.alert_number_model: AlertNumber = self.locator.get_model("AlertNumber")

    def create_alert(self, params: dict) -> Alert:
        def _rollback(vo: Alert) -> None:
            _LOGGER.info(
                f"[create_alert._rollback] "
                f"Delete alert : #{str(vo.alert_number)} "
                f"({vo.alert_id})"
            )
            vo.delete()

        params["alert_number"] = self._get_alert_number(
            params["domain_id"], params["workspace_id"]
        )
        params["alert_number_str"] = str(params["alert_number"])
        alert_vo: Alert = self.alert_model.create(params)
        self.transaction.add_rollback(_rollback, alert_vo)

        return alert_vo

    def update_alert(self, params):
        alert_vo: Alert = self.get_alert(params["alert_id"], params["domain_id"])
        return self.update_alert_by_vo(params, alert_vo)

    def update_alert_by_vo(self, params: dict, alert_vo: Alert) -> Alert:
        def _rollback(old_data: dict):
            _LOGGER.info(
                f"[update_alert_by_vo._rollback] Revert Data : "
                f'{old_data["alert_id"]}'
            )
            alert_vo.update(old_data)

        self.transaction.add_rollback(_rollback, alert_vo.to_dict())
        return alert_vo.update(params)

    def delete_alert(self, alert_id, domain_id, workspace_id, user_projects=None):
        alert_vo: Alert = self.get_alert(
            alert_id, domain_id, workspace_id, user_projects
        )
        alert_vo.delete()

    def get_alert(
        self,
        alert_id: str,
        domain_id: str,
        workspace_id: str = None,
        user_projects: list = None,
    ) -> Alert:
        conditions = {
            "alert_id": alert_id,
            "domain_id": domain_id,
        }

        if workspace_id:
            conditions["workspace_id"] = workspace_id

        if user_projects:
            conditions["project_id"] = user_projects
        return self.alert_model.get(**conditions)

    def list_alerts(self, query: dict) -> dict:
        return self.alert_model.query(**query)

    def stat_alerts(self, query: dict) -> dict:
        return self.alert_model.stat(**query)

    def _get_alert_number(self, domain_id: str, workspace_id: str) -> int:
        def _rollback(vo: AlertNumber):
            _LOGGER.info(f"[_get_alert_number._rollback] Decrement Number: {vo.next}")
            vo.decrement("next", 1)

        alert_number_vos = self.alert_number_model.filter(
            domain_id=domain_id, workspace_id=workspace_id
        )
        if alert_number_vos.count() > 0:
            account_number_vo = alert_number_vos[0].increment("next", 1)
            self.transaction.add_rollback(_rollback, account_number_vo)
        else:
            account_number_vo = self.alert_number_model.create(
                {"domain_id": domain_id, "workspace_id": workspace_id}
            )
            self.transaction.add_rollback(_rollback, account_number_vo)

        return account_number_vo.next
