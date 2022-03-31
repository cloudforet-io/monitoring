import factory
from spaceone.core import utils

from spaceone.monitoring.model import EventRule
from test.factory.event_rule_condition_factory import EventRuleConditionFactory


class EventRuleFactory(factory.mongoengine.MongoEngineFactory):
    class Meta:
        model = EventRule

    event_rule_id = factory.LazyAttribute(lambda o: utils.generate_id('er'))
    name = factory.LazyAttribute(lambda o: utils.random_string())
    order = 1
    conditions = [
        {
            "key": "description",
            "value": "test",
            "operator": "contain"
        }
    ]
    conditions_policy = 'ALL'
    options = {}
    tags = {'xxx': 'yy'}
    scope = 'PROJECT'
    project_id = utils.generate_id('project')
    domain_id = utils.generate_id('domain')
    created_at = factory.Faker('date_time')
