import factory

from spaceone.core import utils
from spaceone.monitoring.model.alert_model import Alert


class AlertFactory(factory.mongoengine.MongoEngineFactory):

    class Meta:
        model = Alert

    alert_id = factory.LazyAttribute(lambda o: utils.generate_id('alert'))
    alert_number = 3220
    title = factory.LazyAttribute(lambda o: utils.random_string())
    state = 'TRIGGERED'
    description = factory.LazyAttribute(lambda o: utils.random_string())
    urgency = 'HIGH'
    severity = 'CRITICAL'
    resource = {}
    additional_info = {}
    escalation_step = 1
    triggered_by = factory.LazyAttribute(lambda o: utils.generate_id('webhook'))
    webhook_id = factory.LazyAttribute(lambda o: utils.generate_id('webhook'))
    escalation_policy_id = factory.LazyAttribute(lambda o: utils.generate_id('ep'))
    project_id = factory.LazyAttribute(lambda o: utils.generate_id('project'))
    domain_id = utils.generate_id('domain', 10)
    created_at = factory.Faker('date_time')
    updated_at = factory.Faker('date_time')
    escalated_at = factory.Faker('date_time')
