import logging

from spaceone.core.manager import BaseManager
from spaceone.monitoring.model.escalation_policy_model import EscalationPolicy

_LOGGER = logging.getLogger(__name__)


class EscalationPolicyManager(BaseManager):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.escalation_policy_model: EscalationPolicy = self.locator.get_model('EscalationPolicy')

    def create_escalation_policy(self, params):
        def _rollback(escalation_policy_vo: EscalationPolicy):
            _LOGGER.info(f'[create_escalation_policy._rollback] '
                         f'Delete escalation policy : {escalation_policy_vo.name} '
                         f'({escalation_policy_vo.escalation_policy_id})')
            escalation_policy_vo.delete()

        escalation_policy_vo: EscalationPolicy = self.escalation_policy_model.create(params)
        self.transaction.add_rollback(_rollback, escalation_policy_vo)

        return escalation_policy_vo

    def update_escalation_policy(self, params):
        escalation_policy_vo: EscalationPolicy = self.get_escalation_policy(params['escalation_policy_id'],
                                                                            params['domain_id'])
        return self.update_escalation_policy_by_vo(params, escalation_policy_vo)

    def update_escalation_policy_by_vo(self, params, escalation_policy_vo):
        def _rollback(old_data):
            _LOGGER.info(f'[update_escalation_policy_by_vo._rollback] Revert Data : '
                         f'{old_data["escalation_policy_id"]}')
            escalation_policy_vo.update(old_data)

        self.transaction.add_rollback(_rollback, escalation_policy_vo.to_dict())

        return escalation_policy_vo.update(params)

    def set_default_escalation_policy(self, params):
        escalation_policy_vos = self.escalation_policy_model.get(domain_id=params['domain_id'])
        updated_escalation_policy_vo = None
        for escalation_policy_vo in escalation_policy_vos:
            if params['escalation_policy_id'] == escalation_policy_vo.escalation_policy_id:
                escalation_policy_vo.update({'is_default': True})
                updated_escalation_policy_vo = escalation_policy_vo
            else:
                escalation_policy_vo.update({'is_default': False})

        return updated_escalation_policy_vo

    def delete_escalation_policy(self, escalation_policy_id, domain_id):
        escalation_policy_vo: EscalationPolicy = self.get_escalation_policy(escalation_policy_id, domain_id)
        escalation_policy_vo.delete()

    def get_escalation_policy(self, escalation_policy_id, domain_id, only=None):
        return self.escalation_policy_model.get(escalation_policy_id=escalation_policy_id,
                                                domain_id=domain_id, only=only)

    def list_escalation_policies(self, query={}):
        return self.escalation_policy_model.query(**query)

    def stat_escalation_policies(self, query):
        return self.escalation_policy_model.stat(**query)
