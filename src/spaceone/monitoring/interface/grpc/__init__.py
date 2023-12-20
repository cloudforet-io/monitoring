from spaceone.core.pygrpc.server import GRPCServer

from spaceone.monitoring.interface.grpc.alert import Alert
from spaceone.monitoring.interface.grpc.data_source import DataSource
from spaceone.monitoring.interface.grpc.escalation_policy import EscalationPolicy
from spaceone.monitoring.interface.grpc.event import Event
from spaceone.monitoring.interface.grpc.event_rule import EventRule
from spaceone.monitoring.interface.grpc.log import Log
from spaceone.monitoring.interface.grpc.metric import Metric
from spaceone.monitoring.interface.grpc.note import Note
from spaceone.monitoring.interface.grpc.project_alert_config import ProjectAlertConfig
from spaceone.monitoring.interface.grpc.webhook import Webhook

_all_ = ["app"]

app = GRPCServer()
app.add_service(Alert)
app.add_service(DataSource)
app.add_service(EscalationPolicy)
app.add_service(Event)
app.add_service(EventRule)
app.add_service(Log)
app.add_service(Metric)
app.add_service(Note)
app.add_service(ProjectAlertConfig)
app.add_service(Webhook)
