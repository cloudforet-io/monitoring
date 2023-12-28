import logging

from spaceone.core.service import *

from spaceone.monitoring.manager.alert_manager import AlertManager
from spaceone.monitoring.manager.note_manager import NoteManager
from spaceone.monitoring.model import Note

_LOGGER = logging.getLogger(__name__)


@authentication_handler
@authorization_handler
@mutation_handler
@event_handler
class NoteService(BaseService):
    resource = "Note"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.note_mgr: NoteManager = self.locator.get_manager("NoteManager")

    @transaction(
        permission="monitoring:Note.write",
        role_types=["WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @check_required(["alert_id", "note", "domain_id", "workspace_id"])
    def create(self, params: dict) -> Note:
        """Create alert note

        Args:
            params (dict): {
                'alert_id': 'str',        # required
                'note': 'str',            # required
                'domain_id': 'str',       # injected from auth (required)
                'workspace_id': 'str',    # injected from auth (required)
            }

        Returns:
            note_vo (object)
        """

        alert_mgr: AlertManager = self.locator.get_manager("AlertManager")
        alert_vo = alert_mgr.get_alert(
            params["alert_id"], params["domain_id"], params["workspace_id"]
        )

        params["alert"] = alert_vo
        params["project_id"] = alert_vo.project_id
        params["created_by"] = self.transaction.get_meta("authorization.user_id")

        return self.note_mgr.create_note(params)

    @transaction(
        permission="monitoring:Note.write",
        role_types=["WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @check_required(["note_id", "domain_id", "workspace_id"])
    def update(self, params: dict) -> Note:
        """Update alert note

        Args:
            params (dict): {
                'note_id': 'str',         # required
                'note': 'dict',
                'domain_id': 'str',       # injected from auth (required)
                'workspace_id': 'str',    # injected from auth (required)
                'user_projects': 'list',  # injected from auth
            }

        Returns:
            note_vo (object)
        """

        note_id = params["note_id"]
        domain_id = params["domain_id"]
        workspace_id = params["workspace_id"]
        user_projects = params.get("user_projects")

        note_vo = self.note_mgr.get_note(
            note_id, domain_id, workspace_id, user_projects
        )

        # Check permission

        return self.note_mgr.update_note_by_vo(params, note_vo)

    @transaction(
        permission="monitoring:Note.write",
        role_types=["WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @check_required(["note_id", "domain_id", "workspace_id"])
    def delete(self, params):
        """Delete alert note

        Args:
            params (dict): {
                'note_id': 'str',
                'domain_id': 'str',       # injected from auth (required)
                'workspace_id': 'str',    # injected from auth (required)
                'user_projects': 'list',  # injected from auth
            }

        Returns:
            None
        """

        note_vo = self.note_mgr.get_note(
            params["note_id"],
            params["domain_id"],
            params["workspace_id"],
            params.get("user_projects"),
        )

        self.note_mgr.delete_note_by_vo(note_vo)

    @transaction(
        permission="monitoring:Note.read",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @check_required(["note_id", "domain_id", "workspace_id"])
    def get(self, params):
        """Get alert note

        Args:
            params (dict): {
                'note_id': 'str',
                'domain_id': 'str',       # injected from auth (required)
                'workspace_id': 'str',    # injected from auth (required)
                'user_projects': 'list',  # injected from auth
            }

        Returns:
            note_vo (object)
        """

        return self.note_mgr.get_note(
            params["note_id"],
            params["domain_id"],
            params["workspace_id"],
            params.get("user_projects"),
        )

    @transaction(
        permission="monitoring:Note.read",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @check_required(["domain_id"])
    @append_query_filter(
        [
            "note_id",
            "alert_id",
            "created_by",
            "project_id",
            "domain_id",
            "workspace_id",
            "user_projects",
        ]
    )
    @append_keyword_filter(["note_id", "note"])
    def list(self, params):
        """List alert notes

        Args:
            params (dict): {
                'query': 'dict (spaceone.api.core.v1.Query)',
                'note_id': 'str',
                'alert_id': 'str',
                'created_by': 'str',
                'workspace_id': 'str',
                'project_id': 'str',
                'domain_id': 'str',       # injected from auth (required)
                'user_projects': 'list',  # injected from auth
            }

        Returns:
            note_vos (object)
            total_count
        """

        query = params.get("query", {})
        return self.note_mgr.list_notes(query)

    @transaction(
        permission="monitoring:Note.read",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @check_required(["query", "domain_id", "workspace_id"])
    @append_query_filter(["domain_id", "workspace_id", "user_projects"])
    @append_keyword_filter(["note_id", "note"])
    def stat(self, params):
        """
        Args:
            params (dict): {
                'query': 'dict (spaceone.api.core.v1.StatisticsQuery)',
                'domain_id': 'str',          # injected from auth (required)
                'workspace_id': 'str',       # injected from auth (required)
                'user_projects': 'list',     # injected from auth
            }

        Returns:
            values (list) : 'list of statistics data'

        """

        query = params.get("query", {})
        return self.note_mgr.stat_notes(query)
