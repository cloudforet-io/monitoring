from mongoengine import *

from spaceone.core.model.mongo_model import MongoModel


class EscalationRule(EmbeddedDocument):
    notification_level = StringField(max_length=20, default="ALL")
    escalate_minutes = IntField(default=0, min_value=0)

    def to_dict(self):
        return self.to_mongo()


class EscalationPolicy(MongoModel):
    escalation_policy_id = StringField(max_length=40, generate_id="ep", unique=True)
    name = StringField(max_length=255, unique_with=["workspace_id", "domain_id"])
    is_default = BooleanField(default=False)
    rules = ListField(EmbeddedDocumentField(EscalationRule))
    repeat_count = IntField(default=0, min_value=0)
    finish_condition = StringField(
        max_length=20, default="ACKNOWLEDGED", choices=("ACKNOWLEDGED", "RESOLVED")
    )
    tags = DictField()
    resource_group = StringField(max_length=40, choices=("WORKSPACE", "PROJECT"))
    project_id = StringField(max_length=40)
    workspace_id = StringField(max_length=40)
    domain_id = StringField(max_length=40)
    created_at = DateTimeField(auto_now_add=True)

    meta = {
        "updatable_fields": [
            "name",
            "is_default",
            "rules",
            "repeat_count",
            "finish_condition",
            "tags",
        ],
        "minimal_fields": ["escalation_policy_id", "name", "is_default", "project_id"],
        "change_query_keys": {"user_projects": "project_id"},
        "ordering": ["name"],
        "indexes": [
            # 'escalation_policy_id',
            "is_default",
            "finish_condition",
            "resource_group",
            "project_id",
            "workspace_id",
            "domain_id",
        ],
    }
