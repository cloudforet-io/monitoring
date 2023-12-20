from spaceone.core.pygrpc.server import GRPCServer
from spaceone.core.plugin.server import PluginServer
from spaceone.monitoring.plugin.webhook.interface.grpc import app
from spaceone.monitoring.plugin.webhook.service.webhook_service import WebhookService
from spaceone.monitoring.plugin.webhook.service.event_service import EventService

__all__ = ["WebhookPluginServer"]


class WebhookPluginServer(PluginServer):
    _grpc_app: GRPCServer = app
    _global_conf_path: str = (
        "spaceone.monitoring.plugin.webhook.conf.global_conf:global_conf"
    )
    _plugin_methods = {
        "Webhook": {"service": WebhookService, "methods": ["init", "verify"]},
        "Event": {"service": EventService, "methods": ["parse"]},
    }
