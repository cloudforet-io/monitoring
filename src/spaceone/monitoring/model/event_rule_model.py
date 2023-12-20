from mongoengine import *

from spaceone.core.model.mongo_model import MongoModel


class EventRuleCondition(EmbeddedDocument):
    key = StringField(required=True)
    value = StringField(required=True)
    operator = StringField(choices=("eq", "contain", "not", "not_contain"))


class EventRuleOptions(EmbeddedDocument):
    stop_processing = BooleanField(default=False)


class EventRule(MongoModel):
    event_rule_id = StringField(max_length=40, generate_id="er", unique=True)
    name = StringField(max_length=255, default="")
    order = IntField(required=True)
    conditions = ListField(EmbeddedDocumentField(EventRuleCondition))
    conditions_policy = StringField(max_length=20, choices=("ALL", "ANY", "ALWAYS"))
    actions = DictField()
    options = EmbeddedDocumentField(EventRuleOptions, default=EventRuleOptions)
    tags = DictField()
    resource_group = StringField(max_length=40, choices=("WORKSPACE", "PROJECT"))
    project_id = StringField(max_length=40, default=None, null=True)
    domain_id = StringField(max_length=40)
    workspace_id = StringField(max_length=40)
    created_at = DateTimeField(auto_now_add=True)

    meta = {
        "updatable_fields": [
            "name",
            "order",
            "conditions",
            "conditions_policy",
            "actions",
            "options",
            "tags",
        ],
        "minimal_fields": [
            "event_rule_id",
            "name",
            "order",
            "resource_group",
            "project_id",
            "workspace_id",
        ],
        "change_query_keys": {"user_projects": "project_id"},
        "ordering": ["order"],
        "indexes": [
            # 'event_rule_id',
            "order",
            "conditions_policy",
            "resource_group",
            "project_id",
            "workspace_id",
            "domain_id",
        ],
    }
