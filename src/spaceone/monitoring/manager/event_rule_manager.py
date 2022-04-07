import logging
import functools
from typing import List

from spaceone.core import utils
from spaceone.core.manager import BaseManager
from spaceone.monitoring.manager import IdentityManager
from spaceone.monitoring.model.event_rule_model import EventRule, EventRuleCondition

_LOGGER = logging.getLogger(__name__)


class EventRuleManager(BaseManager):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.event_rule_model: EventRule = self.locator.get_model('EventRule')
        self.identity_mgr: IdentityManager = self.locator.get_manager('IdentityManager')
        self._service_account_info = {}

    def create_event_rule(self, params):
        def _rollback(event_rule_vo: EventRule):
            _LOGGER.info(f'[create_event_rule._rollback] '
                         f'Delete event rule : {event_rule_vo.name} '
                         f'({event_rule_vo.event_rule_id})')
            event_rule_vo.delete()

        event_rule_vo: EventRule = self.event_rule_model.create(params)
        self.transaction.add_rollback(_rollback, event_rule_vo)

        return event_rule_vo

    def update_event_rule(self, params):
        event_rule_vo: EventRule = self.get_event_rule(params['event_rule_id'], params['domain_id'])
        return self.update_event_rule_by_vo(params, event_rule_vo)

    def update_event_rule_by_vo(self, params, event_rule_vo):
        def _rollback(old_data):
            _LOGGER.info(f'[update_event_rule_by_vo._rollback] Revert Data : '
                         f'{old_data["event_rule_id"]}')
            event_rule_vo.update(old_data)

        self.transaction.add_rollback(_rollback, event_rule_vo.to_dict())

        return event_rule_vo.update(params)

    def delete_event_rule(self, event_rule_id, domain_id):
        event_rule_vo: EventRule = self.get_event_rule(event_rule_id, domain_id)
        self.delete_event_rule_by_vo(event_rule_vo)

    def delete_event_rule_by_vo(self, event_rule_vo):
        event_rule_vo.delete()

    def get_event_rule(self, event_rule_id, domain_id, only=None):
        return self.event_rule_model.get(event_rule_id=event_rule_id, domain_id=domain_id, only=only)

    def list_event_rules(self, query={}):
        return self.event_rule_model.query(**query)

    def stat_event_rules(self, query):
        return self.event_rule_model.stat(**query)

    def change_event_data(self, event_data, project_id, domain_id):
        event_rule_vos: List[EventRule] = self._get_project_event_rules(project_id, domain_id)

        for event_rule_vo in event_rule_vos:
            is_match = self._change_event_data_by_event_rule(event_data, event_rule_vo)

            if is_match:
                event_data = self._change_event_data_with_actions(event_data, event_rule_vo.actions, domain_id)

            if is_match and event_rule_vo.options.stop_processing:
                break

        # TODO: Check Global Event Rule

        return event_data

    def _change_event_data_with_actions(self, event_data, actions, domain_id):
        for action, value in actions.items():
            if action == 'change_project':
                event_data['project_id'] = value

            if action == 'change_assignee':
                event_data['assignee'] = value

            if action == 'change_urgency':
                event_data['urgency'] = value

            if action == 'add_project_dependency':
                event_data['project_dependencies'] = value

            if action == 'add_responder':
                event_data['responders'] = value

            if action == 'add_additional_info':
                event_data['additional_info'] = event_data.get('additional_info', {})
                event_data['additional_info'].update(value)

            if action == 'no_notification':
                event_data['no_notification'] = value

            if action == 'match_service_account':
                source = value['source']
                target_key = value['target']
                target_value = utils.get_dict_value(event_data, source)
                if target_value:
                    service_account_info = self._get_service_account(target_key, target_value, domain_id)
                    if service_account_info:
                        event_data['project_id'] = service_account_info.get('project_info', {}).get('project_id')

        return event_data

    def _change_event_data_by_event_rule(self, event_data, event_rule_vo: EventRule):
        conditions_policy = event_rule_vo.conditions_policy

        if conditions_policy == 'ALWAYS':
            return True
        else:
            results = list(map(functools.partial(self._check_condition, event_data),
                               event_rule_vo.conditions))

            if conditions_policy == 'ALL':
                return all(results)
            else:
                return any(results)

    @staticmethod
    def _check_condition(event_data, condition: EventRuleCondition):
        event_value = utils.get_dict_value(event_data, condition.key)
        condition_value = condition.value
        operator = condition.operator

        if event_value is None:
            return False

        if operator == 'eq':
            if event_value == condition_value:
                return True
            else:
                return False
        elif operator == 'contain':
            if event_value.lower().find(condition_value.lower()) >= 0:
                return True
            else:
                return False
        elif operator == 'not':
            if event_value != condition_value:
                return True
            else:
                return False
        elif operator == 'not_contain':
            if event_value.lower().find(condition_value.lower()) < 0:
                return True
            else:
                return False

        return False

    def _get_project_event_rules(self, project_id, domain_id):
        query = {
            'filter': [
                {
                    'k': 'project_id',
                    'v': project_id,
                    'o': 'eq'
                },
                {
                    'k': 'domain_id',
                    'v': domain_id,
                    'o': 'eq'
                }
            ],
            'sort': {
                'key': 'order'
            }
        }

        event_rule_vos, total_count = self.list_event_rules(query)
        return event_rule_vos

    def _get_service_account(self, target_key, target_value, domain_id):
        if f'{domain_id}:{target_key}:{target_value}' in self._service_account_info:
            return self._service_account_info[f'{domain_id}:{target_key}:{target_value}']

        query = {
            'filter': [
                {'k': target_key, 'v': target_value, 'o': 'eq'}
            ],
            'only': ['service_account_id', 'project_info']
        }

        response = self.identity_mgr.list_service_accounts(query, domain_id)
        results = response.get('results', [])
        total_count = response.get('total_count', 0)

        service_account_info = None
        if total_count > 0:
            service_account_info = results[0]

        self._service_account_info[f'{domain_id}:{target_key}:{target_value}'] = service_account_info
        return service_account_info
