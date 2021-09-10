import functools
from spaceone.api.monitoring.v1 import webhook_pb2
from spaceone.core.pygrpc.message_type import *
from spaceone.core import utils
from spaceone.core import config
from spaceone.monitoring.model.webhook_model import Webhook

__all__ = ['WebhookInfo', 'WebhooksInfo']


def PluginInfo(vo):
    if vo:
        info = {
            'plugin_id': vo.plugin_id,
            'version': vo.version,
            'options': change_struct_type(vo.options),
            'metadata': change_struct_type(vo.metadata),
            'upgrade_mode': vo.upgrade_mode
        }

        return webhook_pb2.WebhookPluginInfo(**info)
    else:
        return None


def WebhookInfo(webhook_vo: Webhook, minimal=False):
    if webhook_vo.webhook_url:
        webhook_url = f'{config.get_global("WEBHOOK_DOMAIN")}{webhook_vo.webhook_url}'
    else:
        webhook_url = None

    info = {
        'webhook_id': webhook_vo.webhook_id,
        'name': webhook_vo.name,
        'state': webhook_vo.state,
        'webhook_url': webhook_url,
        'project_id': webhook_vo.project_id
    }

    if not minimal:
        info.update({
            'access_key': webhook_vo.access_key,
            'capability': change_struct_type(webhook_vo.capability),
            'plugin_info': PluginInfo(webhook_vo.plugin_info),
            'domain_id': webhook_vo.domain_id,
            'created_at': utils.datetime_to_iso8601(webhook_vo.created_at)
        })

    return webhook_pb2.WebhookInfo(**info)


def WebhooksInfo(webhook_vos, total_count, **kwargs):
    return webhook_pb2.WebhooksInfo(results=list(
        map(functools.partial(WebhookInfo, **kwargs), webhook_vos)), total_count=total_count)
