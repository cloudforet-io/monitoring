from mongoengine import *

from spaceone.core.model.mongo_model import MongoModel


class AlertResource(EmbeddedDocument):
    resource_id = StringField(default=None, null=True)
    resource_type = StringField(default=None, null=True)
    name = StringField(default=None, null=True)


class AlertNumber(MongoModel):
    next = IntField(default=1)
    workspace_id = StringField(max_length=40)
    domain_id = StringField(max_length=40)


class Alert(MongoModel):
    alert_number = IntField(required=True)
    alert_number_str = StringField()
    alert_id = StringField(max_length=40, generate_id="alert", unique=True)
    title = StringField()
    state = StringField(
        max_length=20,
        default="TRIGGERED",
        choices=("TRIGGERED", "ACKNOWLEDGED", "RESOLVED", "ERROR"),
    )
    description = StringField(default=None, null=True)
    assignee = StringField(default=None, null=True)
    urgency = StringField(max_length=20, default="HIGH", choices=("HIGH", "LOW"))
    severity = StringField(
        max_length=20,
        default="NONE",
        choices=("CRITICAL", "ERROR", "WARNING", "INFO", "NOT_AVAILABLE", "NONE"),
    )
    rule = StringField(default=None, null=True)
    image_url = StringField(default=None, null=True)
    resource = EmbeddedDocumentField(AlertResource, default=None, null=True)
    provider = StringField(default=None, null=True)
    account = StringField(default=None, null=True)
    additional_info = DictField()
    escalation_step = IntField(default=1)
    escalation_ttl = IntField(default=0)
    triggered_by = StringField(default=None, null=True)
    webhook_id = StringField(max_length=40, default=None, null=True)
    escalation_policy_id = StringField(max_length=40)
    project_id = StringField(max_length=40)
    workspace_id = StringField(max_length=40)
    domain_id = StringField(max_length=40)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    acknowledged_at = DateTimeField(default=None, null=True)
    resolved_at = DateTimeField(default=None, null=True)
    escalated_at = DateTimeField(default=None, null=True)

    meta = {
        "updatable_fields": [
            "title",
            "state",
            "description",
            "assignee",
            "urgency",
            "escalation_step",
            "escalation_ttl",
            "escalation_policy_id",
            "project_id",
            "acknowledged_at",
            "resolved_at",
            "escalated_at",
        ],
        "minimal_fields": [
            "alert_number",
            "alert_id",
            "title",
            "state",
            "assignee",
            "urgency",
            "escalation_step",
            "escalation_ttl",
            "project_id",
        ],
        "change_query_keys": {
            "resource_id": "resource.resource_id",
            "user_projects": "project_id",
        },
        "ordering": ["-created_at"],
        "indexes": [
            "alert_number",
            # 'alert_id',
            "state",
            "assignee",
            "urgency",
            "severity",
            "resource.resource_id",
            "resource.resource_type",
            "resource.name",
            "provider",
            "account",
            "escalation_step",
            "triggered_by",
            "webhook_id",
            "escalation_policy_id",
            "project_id",
            "workspace_id",
            "domain_id",
            "created_at",
            "acknowledged_at",
            "resolved_at",
            "escalated_at",
            {
                "fields": [
                    "domain_id",
                    "workspace_id",
                    "state",
                    "escalation_step",
                    "escalation_ttl",
                    "escalation_policy_id",
                    "escalated_at",
                ],
                "name": "COMPOUND_INDEX_FOR_ESCALATION",
            },
        ],
    }
