import copy
import logging

from spaceone.core import cache
from spaceone.core.manager import BaseManager
from spaceone.monitoring.error.escalation_policy import *
from spaceone.monitoring.model.escalation_policy_model import EscalationPolicy
from spaceone.monitoring.conf.default_escalation_policy import DEFAULT_ESCALATION_POLICY

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

        updated_vo: EscalationPolicy = escalation_policy_vo.update(params)

        cache.delete(f'escalation-policy-condition:{updated_vo.domain_id}:{updated_vo.escalation_policy_id}')

        return updated_vo

    def set_default_escalation_policy(self, params, escalation_policy_vo):
        global_escalation_policy_vos = self.escalation_policy_model.filter(domain_id=params['domain_id'],
                                                                           scope='DOMAIN')

        for global_escalation_policy_vo in global_escalation_policy_vos:
            global_escalation_policy_vo.update({'is_default': False})

        return escalation_policy_vo.update({'is_default': True})

    def get_default_escalation_policy(self, domain_id):
        escalation_policy_vos = self.escalation_policy_model.filter(is_default=True, domain_id=domain_id)
        if escalation_policy_vos.count() > 0:
            return escalation_policy_vos[0]
        else:
            default_escalation_policy = copy.deepcopy(DEFAULT_ESCALATION_POLICY)
            default_escalation_policy['domain_id'] = domain_id
            return self.create_escalation_policy(default_escalation_policy)

    def delete_escalation_policy(self, escalation_policy_id, domain_id):
        escalation_policy_vo: EscalationPolicy = self.get_escalation_policy(escalation_policy_id, domain_id)

        if escalation_policy_vo.is_default:
            raise ERROR_DEFAULT_ESCALATION_POLICY_NOT_ALLOW_DELETION(escalation_policy_id=escalation_policy_id)

        cache.delete(f'escalation-policy-condition:{domain_id}:{escalation_policy_id}')

        escalation_policy_vo.delete()

    def get_escalation_policy(self, escalation_policy_id, domain_id, only=None):
        return self.escalation_policy_model.get(escalation_policy_id=escalation_policy_id,
                                                domain_id=domain_id, only=only)

    def list_escalation_policies(self, query={}):
        return self.escalation_policy_model.query(**query)

    def stat_escalation_policies(self, query):
        return self.escalation_policy_model.stat(**query)
