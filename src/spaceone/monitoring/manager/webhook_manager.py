import logging

from spaceone.core import cache
from spaceone.core.manager import BaseManager
from spaceone.monitoring.model.webhook_model import Webhook

_LOGGER = logging.getLogger(__name__)


class WebhookManager(BaseManager):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.webhook_model: Webhook = self.locator.get_model('Webhook')

    def create_webhook(self, params):
        def _rollback(webhook_vo):
            _LOGGER.info(f'[create_webhook._rollback] '
                         f'Delete webhook : {webhook_vo.name} '
                         f'({webhook_vo.webhook_id})')
            webhook_vo.delete()

        webhook_vo: Webhook = self.webhook_model.create(params)
        self.transaction.add_rollback(_rollback, webhook_vo)

        return webhook_vo

    def update_webhook(self, params):
        webhook_vo: Webhook = self.get_webhook(params['webhook_id'], params['domain_id'])
        return self.update_webhook_by_vo(params, webhook_vo)

    def update_webhook_by_vo(self, params, webhook_vo):
        def _rollback(old_data):
            _LOGGER.info(f'[update_webhook_by_vo._rollback] Revert Data : '
                         f'{old_data["webhook_id"]}')
            webhook_vo.update(old_data)

        self.transaction.add_rollback(_rollback, webhook_vo.to_dict())

        updated_vo: Webhook = webhook_vo.update(params)

        cache.delete(f'webhook-data:{updated_vo.webhook_id}')

        return updated_vo

    def delete_webhook(self, webhook_id, domain_id):
        webhook_vo: Webhook = self.get_webhook(webhook_id, domain_id)

        cache.delete(f'webhook-data:{webhook_vo.webhook_id}')

        webhook_vo.delete()

    def get_webhook(self, webhook_id, domain_id, only=None):
        return self.webhook_model.get(webhook_id=webhook_id, domain_id=domain_id, only=only)

    def get_webhook_by_id(self, webhook_id):
        return self.webhook_model.get(webhook_id=webhook_id)

    def list_webhooks(self, query={}):
        return self.webhook_model.query(**query)

    def stat_webhooks(self, query):
        return self.webhook_model.stat(**query)
