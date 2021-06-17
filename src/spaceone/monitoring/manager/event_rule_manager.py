import logging

from spaceone.monitoring.error.event_rule import *
from spaceone.core.manager import BaseManager
from spaceone.monitoring.model.event_rule_model import EventRule

_LOGGER = logging.getLogger(__name__)


class EventRuleManager(BaseManager):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.event_rule_model: EventRule = self.locator.get_model('EventRule')

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
