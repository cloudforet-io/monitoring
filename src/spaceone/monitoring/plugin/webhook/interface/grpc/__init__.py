from spaceone.core.pygrpc.server import GRPCServer
from spaceone.monitoring.plugin.webhook.interface.grpc.event import Event
from spaceone.monitoring.plugin.webhook.interface.grpc.webhook import Webhook

_all_ = ["app"]

app = GRPCServer()
app.add_service(Event)
app.add_service(Webhook)
