import logging

from spaceone.core.service import *
from spaceone.monitoring.model.note_model import Note
from spaceone.monitoring.manager.alert_manager import AlertManager
from spaceone.monitoring.manager.note_manager import NoteManager

_LOGGER = logging.getLogger(__name__)


@authentication_handler
@authorization_handler
@mutation_handler
@event_handler
class NoteService(BaseService):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.note_mgr: NoteManager = self.locator.get_manager('NoteManager')

    @transaction(append_meta={'authorization.scope': 'PROJECT'})
    @check_required(['alert_id', 'note', 'domain_id'])
    def create(self, params):
        """Create alert note

        Args:
            params (dict): {
                'alert_id': 'str',
                'note': 'str',
                'domain_id': 'str'
            }

        Returns:
            note_vo (object)
        """

        user_id = self.transaction.get_meta('user_id')

        alert_mgr: AlertManager = self.locator.get_manager('AlertManager')
        alert_vo = alert_mgr.get_alert(params['alert_id'], params['domain_id'])

        params['alert'] = alert_vo
        params['project_id'] = alert_vo.project_id
        params['created_by'] = user_id

        return self.note_mgr.create_note(params)

    @transaction(append_meta={'authorization.scope': 'PROJECT'})
    @check_required(['note_id', 'domain_id'])
    def update(self, params):
        """Update alert note

        Args:
            params (dict): {
                'note_id': 'str',
                'note': 'dict',
                'domain_id': 'str'
            }

        Returns:
            note_vo (object)
        """
        
        note_id = params['note_id']
        domain_id = params['domain_id']

        note_vo = self.note_mgr.get_note(note_id, domain_id)

        # Check permission

        return self.note_mgr.update_note_by_vo(params, note_vo)

    @transaction(append_meta={'authorization.scope': 'PROJECT'})
    @check_required(['note_id', 'domain_id'])
    def delete(self, params):
        """Delete alert note

        Args:
            params (dict): {
                'note_id': 'str',
                'domain_id': 'str'
            }

        Returns:
            None
        """

        self.note_mgr.delete_note(params['note_id'], params['domain_id'])

    @transaction(append_meta={'authorization.scope': 'PROJECT'})
    @check_required(['note_id', 'domain_id'])
    def get(self, params):
        """ Get alert note

        Args:
            params (dict): {
                'note_id': 'str',
                'domain_id': 'str',
                'only': 'list
            }

        Returns:
            note_vo (object)
        """

        return self.note_mgr.get_note(params['note_id'], params['domain_id'], params.get('only'))

    @transaction(append_meta={'authorization.scope': 'PROJECT'})
    @check_required(['domain_id'])
    @append_query_filter(['note_id', 'alert_id', 'created_by', 'project_id', 'domain_id', 'user_projects'])
    @append_keyword_filter(['note_id', 'note'])
    def list(self, params):
        """ List alert notes

        Args:
            params (dict): {
                'note_id': 'str',
                'alert_id': 'str',
                'created_by': 'str',
                'project_id': 'str',
                'domain_id': 'str',
                'query': 'dict (spaceone.api.core.v1.Query)',
                'user_projects': 'list', // from meta
            }

        Returns:
            note_vos (object)
            total_count
        """

        query = params.get('query', {})
        return self.note_mgr.list_notes(query)

    @transaction(append_meta={'authorization.scope': 'PROJECT'})
    @check_required(['query', 'domain_id'])
    @append_query_filter(['domain_id', 'user_projects'])
    @append_keyword_filter(['note_id', 'note'])
    def stat(self, params):
        """
        Args:
            params (dict): {
                'domain_id': 'str',
                'query': 'dict (spaceone.api.core.v1.StatisticsQuery)',
                'user_projects': 'list', // from meta
            }

        Returns:
            values (list) : 'list of statistics data'

        """

        query = params.get('query', {})
        return self.note_mgr.stat_notes(query)
