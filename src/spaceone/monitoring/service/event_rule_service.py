import logging
import fnmatch

from spaceone.core.service import *
from spaceone.monitoring.error.event_rule import *
from spaceone.monitoring.model.event_rule_model import EventRule
from spaceone.monitoring.manager.identity_manager import IdentityManager
from spaceone.monitoring.manager.event_rule_manager import EventRuleManager

_LOGGER = logging.getLogger(__name__)

_SUPPORTED_CONDITION_KEYS = ['title', 'description', 'rule', 'resource_id', 'resource_name', 'resource_type',
                             'webhook_id', 'project_id', 'additional_info.<key>']
_SUPPORTED_CONDITION_OPERATORS = ['eq', 'contain', 'not', 'not_contain']


@authentication_handler
@authorization_handler
@mutation_handler
@event_handler
class EventRuleService(BaseService):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.event_rule_mgr: EventRuleManager = self.locator.get_manager('EventRuleManager')

    @transaction(append_meta={
        'authorization.scope': 'PROJECT',
        'authorization.require_project_id': True
    })
    @check_required(['conditions', 'conditions_policy', 'actions'])
    def create(self, params):
        """Create event rule

        Args:
            params (dict): {
                'name': 'str',
                'conditions': 'list',
                'conditions_policy': 'str',
                'actions': 'dict',
                'options': 'dict',
                'project_id': 'str',
                'tags': 'dict',
                'domain_id': 'str'
            }

        Returns:
            event_rule_vo (object)
        """

        project_id = params.get('project_id')
        domain_id = params['domain_id']

        identity_mgr: IdentityManager = self.locator.get_manager('IdentityManager')

        if project_id:
            identity_mgr.get_project(project_id, domain_id)
            params['scope'] = 'PROJECT'
        else:
            params['scope'] = 'GLOBAL'

        self._check_conditions(params['conditions'])
        self._check_actions(params['actions'])

        params['order'] = self._get_highest_order(params['scope'], params.get('project_id'), params['domain_id']) + 1

        return self.event_rule_mgr.create_event_rule(params)

    @transaction(append_meta={'authorization.scope': 'PROJECT'})
    @check_required(['event_rule_id', 'domain_id'])
    def update(self, params):
        """Update event rule

        Args:
            params (dict): {
                'event_rule_id': 'dict',
                'name': 'str',
                'conditions': 'list',
                'conditions_policy': 'str',
                'actions': 'dict',
                'options': 'dict',
                'tags': 'dict',
                'domain_id': 'str'
            }

        Returns:
            event_rule_vo (object)
        """

        event_rule_id = params['event_rule_id']
        domain_id = params['domain_id']

        if 'conditions' in params:
            self._check_conditions(params['conditions'])

        if 'actions' in params:
            self._check_actions(params['actions'])

        event_rule_vo = self.event_rule_mgr.get_event_rule(event_rule_id, domain_id)
        return self.event_rule_mgr.update_event_rule_by_vo(params, event_rule_vo)

    @transaction(append_meta={'authorization.scope': 'PROJECT'})
    @check_required(['event_rule_id', 'order', 'domain_id'])
    def change_order(self, params):
        """ Get event rule

        Args:
            params (dict): {
                'event_rule_id': 'str',
                'order': 'int',
                'domain_id': 'str'
            }

        Returns:
            event_rule_vo (object)
        """

        event_rule_id = params['event_rule_id']
        order = params['order']
        domain_id = params['domain_id']

        self._check_order(order)

        target_event_rule_vo = self.event_rule_mgr.get_event_rule(event_rule_id, domain_id)

        if target_event_rule_vo.order == order:
            return target_event_rule_vo

        highest_order = self._get_highest_order(target_event_rule_vo.scope, target_event_rule_vo.project_id,
                                                target_event_rule_vo.domain_id)

        if order > highest_order:
            raise ERROR_INVALID_PARAMETER(key='order',
                                          reason=f'There is no event rules greater than the {str(order)} order.')

        event_rule_vos = self._get_all_event_rules(target_event_rule_vo.scope, target_event_rule_vo.project_id,
                                                   domain_id, target_event_rule_vo.event_rule_id)
        event_rule_vos.insert(order-1, target_event_rule_vo)

        i = 0
        for event_rule_vo in event_rule_vos:
            if target_event_rule_vo != event_rule_vo:
                self.event_rule_mgr.update_event_rule_by_vo({'order': i+1}, event_rule_vo)

            i += 1

        return self.event_rule_mgr.update_event_rule_by_vo({'order': order}, target_event_rule_vo)

    @transaction(append_meta={'authorization.scope': 'PROJECT'})
    @check_required(['event_rule_id', 'domain_id'])
    def delete(self, params):
        """Delete event rule

        Args:
            params (dict): {
                'event_rule_id': 'str',
                'domain_id': 'str'
            }

        Returns:
            None
        """

        event_rule_id = params['event_rule_id']
        domain_id = params['domain_id']

        event_rule_vo: EventRule = self.event_rule_mgr.get_event_rule(event_rule_id, domain_id)

        scope = event_rule_vo.scope
        project_id = event_rule_vo.project_id

        self.event_rule_mgr.delete_event_rule_by_vo(event_rule_vo)

        event_rule_vos = self._get_all_event_rules(scope, project_id, domain_id)

        i = 0
        for event_rule_vo in event_rule_vos:
            self.event_rule_mgr.update_event_rule_by_vo({'order': i+1}, event_rule_vo)
            i += 1

    @transaction(append_meta={'authorization.scope': 'PROJECT'})
    @check_required(['event_rule_id', 'domain_id'])
    def get(self, params):
        """ Get event rule

        Args:
            params (dict): {
                'event_rule_id': 'str',
                'domain_id': 'str',
                'only': 'list
            }

        Returns:
            event_rule_vo (object)
        """

        return self.event_rule_mgr.get_event_rule(params['event_rule_id'], params['domain_id'], params.get('only'))

    @transaction(append_meta={
        'authorization.scope': 'PROJECT',
        'mutation.append_parameter': {'user_projects': 'authorization.projects'}
    })
    @check_required(['domain_id'])
    @append_query_filter(['event_rule_id', 'name', 'scope', 'project_id', 'domain_id', 'user_projects'])
    @append_keyword_filter(['event_rule_id', 'name'])
    def list(self, params):
        """ List escalation polices

        Args:
            params (dict): {
                'event_rule_id': 'str',
                'name': 'str',
                'scope': 'str',
                'project_id': 'str',
                'domain_id': 'str',
                'query': 'dict (spaceone.api.core.v1.Query)',
                'user_projects': 'list', // from meta
            }

        Returns:
            event_rule_vos (object)
            total_count
        """

        query = params.get('query', {})
        return self.event_rule_mgr.list_event_rules(query)

    @transaction(append_meta={
        'authorization.scope': 'PROJECT',
        'mutation.append_parameter': {'user_projects': 'authorization.projects'}
    })
    @check_required(['query', 'domain_id'])
    @append_query_filter(['domain_id', 'user_projects'])
    @append_keyword_filter(['event_rule_id', 'name'])
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
        return self.event_rule_mgr.stat_event_rules(query)

    @staticmethod
    def _check_conditions(conditions):
        for condition in conditions:
            key = condition.get('key')
            value = condition.get('value')
            operator = condition.get('operator')

            if not (key and value and operator):
                raise ERROR_INVALID_PARAMETER(key='conditions', reason='Condition should have key, value and operator.')

            if key not in _SUPPORTED_CONDITION_KEYS and not fnmatch.fnmatch(key, 'additional_info.*'):
                raise ERROR_INVALID_PARAMETER(key='conditions.key',
                                              reason=f'Unsupported key. '
                                                     f'({" | ".join(_SUPPORTED_CONDITION_KEYS)})')
            if operator not in _SUPPORTED_CONDITION_OPERATORS:
                raise ERROR_INVALID_PARAMETER(key='conditions.operator',
                                              reason=f'Unsupported operator. '
                                                     f'({" | ".join(_SUPPORTED_CONDITION_OPERATORS)})')

    @staticmethod
    def _check_actions(actions):
        if 'change_assignee' in actions:
            # Check User
            pass

        if 'change_urgency' in actions:
            if actions['change_urgency'] not in ['HIGH', 'LOW']:
                raise ERROR_INVALID_PARAMETER(key='actions.change_urgency',
                                              reason=f'Unsupported urgency. (HIGH | LOW)')

        if 'change_project' in actions:
            # Check Project
            pass

        for project_id in actions.get('add_project_dependency', []):
            # Check Project
            pass

        for responder in actions.get('add_responder', []):
            # Check User
            pass

    @staticmethod
    def _check_order(order):
        if order <= 0:
            raise ERROR_INVALID_PARAMETER(key='order', reason='The order must be greater than 0.')

    def _get_highest_order(self, scope, project_id, domain_id):
        query = {
            'filter': [
                {
                    'k': 'domain_id',
                    'v': domain_id,
                    'o': 'eq'
                },
                {
                    'k': 'scope',
                    'v': scope,
                    'o': 'eq'
                },
                {
                    'k': 'project_id',
                    'v': project_id,
                    'o': 'eq'
                }
            ],
            'count_only': True
        }

        event_rule_vos, total_count = self.event_rule_mgr.list_event_rules(query)
        return total_count

    def _get_all_event_rules(self, scope, project_id, domain_id, exclude_event_rule_id=None):

        query = {
            'filter': [
                {
                    'k': 'domain_id',
                    'v': domain_id,
                    'o': 'eq'
                },
                {
                    'k': 'scope',
                    'v': scope,
                    'o': 'eq'
                },
                {
                    'k': 'project_id',
                    'v': project_id,
                    'o': 'eq'
                },
            ],
            'sort': {
                'key': 'order'
            }
        }
        if exclude_event_rule_id is not None:
            query['filter'].append({
                'k': 'event_rule_id',
                'v': exclude_event_rule_id,
                'o': 'not'
            })

        event_rule_vos, total_count = self.event_rule_mgr.list_event_rules(query)
        return list(event_rule_vos)
