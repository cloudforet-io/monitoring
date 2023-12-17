import factory

from spaceone.core import utils
from spaceone.monitoring.model.event_model import Event


class EventFactory(factory.mongoengine.MongoEngineFactory):
    class Meta:
        model = Event

    event_id = factory.LazyAttribute(lambda o: utils.generate_id("event"))
    event_key = utils.random_string()
    event_type = "ALERT"
    title = "TRIGGERED"
    description = factory.LazyAttribute(lambda o: utils.random_string())
    urgency = "HIGH"
    severity = "CRITICAL"
    resource = {}
    rule = utils.random_string()
    raw_data = {}
    alert_id = factory.LazyAttribute(lambda o: utils.generate_id("alert"))
    webhook_id = factory.LazyAttribute(lambda o: utils.generate_id("webhook"))
    project_id = factory.LazyAttribute(lambda o: utils.generate_id("project"))
    domain_id = utils.generate_id("domain", 10)
    created_at = factory.Faker("date_time")
    updated_at = factory.Faker("date_time")
