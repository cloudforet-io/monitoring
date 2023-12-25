import logging

from spaceone.core import config
from spaceone.core.connector.space_connector import SpaceConnector
from spaceone.core.manager import BaseManager

_LOGGER = logging.getLogger(__name__)


class IdentityManager(BaseManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.identity_connector: SpaceConnector = self.locator.get_connector(
            "SpaceConnector", service="identity"
        )

    def get_domain(self, domain_id):
        return self.identity_connector.dispatch("Domain.get", {"domain_id": domain_id})

    def get_domain_by_system_token(self, domain_id):
        system_token = config.get_global("TOKEN")
        return self.identity_connector.dispatch(
            "Domain.get",
            {"domain_id": domain_id},
            token=system_token,
            x_domain_id=domain_id,
        )

    def get_user(self, user_id):
        return self.identity_connector.dispatch("User.get", {"user_id": user_id})

    def get_project(self, project_id: str) -> dict:
        return self.identity_connector.dispatch(
            "Project.get", {"project_id": project_id}
        )

    def get_project_group(self, project_group_id: str) -> dict:
        return self.identity_connector.dispatch(
            "ProjectGroup.get", {"project_group_id": project_group_id}
        )

    def check_workspace(self, workspace_id: str, domain_id: str) -> dict:
        return self.identity_connector.dispatch(
            "Workspace.check", {"workspace_id": workspace_id, "domain_id": domain_id}
        )

    def get_service_account(self, service_account_id, domain_id):
        return self.identity_connector.dispatch(
            "ServiceAccount.get",
            {"service_account_id": service_account_id, "domain_id": domain_id},
        )
