import factory

from spaceone.core import utils
from spaceone.monitoring.model.event_rule_model import EventRuleCondition


class EventRuleConditionFactory(factory.mongoengine.MongoEngineFactory):

    class Meta:
        model = EventRuleCondition

    key = 'description'
    value = 'test'
    operator = 'contain'
