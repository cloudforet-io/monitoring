import logging

from spaceone.core.auth.jwt.jwt_util import JWTUtil
from spaceone.core.connector.space_connector import SpaceConnector
from spaceone.core.manager import BaseManager

_LOGGER = logging.getLogger(__name__)


class IdentityManager(BaseManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        token = self.transaction.get_meta("token")
        self.token_type = self.token_type = JWTUtil.get_value_from_token(token, "typ")
        self.identity_connector: SpaceConnector = self.locator.get_connector(
            "SpaceConnector", service="identity"
        )

    def get_domain(self, domain_id: str) -> dict:
        if self.token_type == "SYSTEM_TOKEN":
            return self.identity_connector.dispatch(
                "Domain.get",
                {"domain_id": domain_id},
                x_domain_id=domain_id,
            )
        else:
            return self.identity_connector.dispatch(
                "Domain.get", {"domain_id": domain_id}
            )

    def get_user(self, user_id: str, domain_id) -> dict:
        if self.token_type == "SYSTEM_TOKEN":
            return self.identity_connector.dispatch(
                "User.get",
                {"user_id": user_id},
                x_domain_id=domain_id,
            )
        else:
            return self.identity_connector.dispatch("User.get", {"user_id": user_id})

    def get_workspace_user(self, user_id: str):
        return self.identity_connector.dispatch(
            "WorkspaceUser.get",
            {"user_id": user_id},
        )

    def get_project(self, project_id: str, domain_id: str = None) -> dict:
        if self.token_type == "SYSTEM_TOKEN":
            return self.identity_connector.dispatch(
                "Project.get",
                {"project_id": project_id},
                x_domain_id=domain_id,
            )
        else:
            return self.identity_connector.dispatch(
                "Project.get", {"project_id": project_id}
            )

    def get_project_group(self, project_group_id: str, domain_id: str) -> dict:
        if self.token_type == "SYSTEM_TOKEN":
            return self.identity_connector.dispatch(
                "ProjectGroup.get",
                {"project_group_id": project_group_id},
                x_domain_id=domain_id,
            )
        else:
            return self.identity_connector.dispatch(
                "ProjectGroup.get", {"project_group_id": project_group_id}
            )

    def check_workspace(self, workspace_id: str, domain_id: str) -> dict:
        system_token = self.transaction.get_meta("token")

        return self.identity_connector.dispatch(
            "Workspace.check",
            {"workspace_id": workspace_id, "domain_id": domain_id},
            token=system_token,
        )
