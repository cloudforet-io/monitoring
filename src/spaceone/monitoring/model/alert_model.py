from mongoengine import *

from spaceone.core.model.mongo_model import MongoModel


class Responder(EmbeddedDocument):
    resource_type = StringField(max_length=255)
    resource_id = StringField(max_length=255)


class AlertResource(EmbeddedDocument):
    resource_id = StringField(default=None, null=True)
    resource_type = StringField(default=None, null=True)
    name = StringField(default=None, null=True)


class Alert(MongoModel):
    alert_number = SequenceField()
    alert_id = StringField(max_length=40, generate_id='alert', unique=True)
    title = StringField()
    state = StringField(max_length=20, default='TRIGGERED', choices=('TRIGGERED', 'ACKNOWLEDGED', 'RESOLVED', 'ERROR'))
    status_message = StringField(default=None, null=True)
    description = StringField(default=None, null=True)
    assignee = StringField(default=None, null=True)
    urgency = StringField(max_length=20, default='HIGH', choices=('HIGH', 'LOW'))
    severity = StringField(max_length=20, default='NONE', choices=('CRITICAL', 'ERROR', 'WARNING', 'INFO',
                                                                   'NOT_AVAILABLE', 'NONE'))
    rule = StringField(default=None, null=True)
    image_url = StringField(default=None, null=True)
    resource = EmbeddedDocumentField(AlertResource, default=None, null=True)
    additional_info = DictField()
    is_snoozed = BooleanField(default=False)
    snoozed_end_time = DateTimeField(default=None, null=True)
    escalation_step = IntField(default=1)
    escalation_ttl = IntField(default=0)
    responders = ListField(EmbeddedDocumentField(Responder))
    project_dependencies = ListField(StringField(max_length=40))
    triggered_by = StringField(default=None, null=True)
    webhook_id = StringField(max_length=40, default=None, null=True)
    escalation_policy_id = StringField(max_length=40)
    project_id = StringField(max_length=40)
    domain_id = StringField(max_length=40)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    acknowledged_at = DateTimeField(default=None, null=True)
    resolved_at = DateTimeField(default=None, null=True)
    escalated_at = DateTimeField(default=None, null=True)

    meta = {
        'updatable_fields': [
            'title',
            'state',
            'status_message',
            'description',
            'assignee',
            'urgency',
            'is_snoozed',
            'snoozed_end_time',
            'escalation_step',
            'escalation_ttl',
            'responders',
            'project_dependencies',
            'escalation_policy_id',
            'project_id',
            'acknowledged_at',
            'resolved_at',
            'escalated_at'
        ],
        'minimal_fields': [
            'alert_number',
            'alert_id',
            'title',
            'state',
            'status_message',
            'assignee',
            'urgency',
            'escalation_step',
            'escalation_ttl',
            'project_id'
        ],
        'change_query_keys': {
            'resource_id': 'resource.resource_id',
            'user_projects': 'project_id'
        },
        'ordering': [
            '-created_at'
        ],
        'indexes': [
            'alert_number',
            'alert_id',
            'state',
            'assignee',
            'urgency',
            'severity',
            'is_snoozed',
            'snoozed_end_time',
            'resource.resource_id',
            'resource.resource_type',
            'resource.name',
            'escalation_step',
            'responders.resource_type',
            'responders.resource_id',
            'project_dependencies',
            'triggered_by',
            'webhook_id',
            'escalation_policy_id',
            'project_id',
            'domain_id',
            'created_at',
            'acknowledged_at',
            'resolved_at',
            'escalated_at',
            {
                "fields": ['domain_id', 'state', 'is_snoozed', 'escalation_step', 'escalation_ttl',
                           'escalation_policy_id', 'escalated_at'],
                "name": "COMPOUND_INDEX_FOR_ESCALATION"
            },
        ]
    }
