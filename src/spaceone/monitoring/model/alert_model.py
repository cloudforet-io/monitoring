from mongoengine import *

from spaceone.core.model.mongo_model import MongoModel


class Responder(EmbeddedDocument):
    resource_type = StringField(max_length=255)
    resource_id = StringField(max_length=255)


class Alert(MongoModel):
    alert_number = SequenceField()
    alert_id = StringField(max_length=40, generate_id='alert', unique=True)
    title = StringField()
    state = StringField(max_length=20, default='TRIGGERED', choices=('TRIGGERED', 'ACKNOWLEDGED', 'RESOLVED'))
    status_message = StringField(default='')
    description = StringField(default='')
    assignee = StringField(default='')
    urgency = StringField(max_length=20, default='HIGH', choices=('HIGH', 'LOW'))
    severity = StringField(max_length=20, default='NONE', choices=('CRITICAL', 'ERROR', 'WARNING', 'INFO',
                                                                   'NOT_AVAILABLE', 'NONE'))
    is_snoozed = BooleanField(default=False)
    snoozed_end_time = DateTimeField(default=None, null=True)
    escalation_level = IntField(default=1)
    escalation_ttl = IntField(default=0)
    responders = ListField(EmbeddedDocumentField(Responder))
    webhook_id = StringField(max_length=40)
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
            'escalation_level',
            'escalation_ttl',
            'responders',
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
            'escalation_level',
            'project_id'
        ],
        'indexes': [
            'alert_number',
            'alert_id',
            'state',
            'assignee',
            'urgency',
            'severity',
            'is_snoozed',
            'escalation_level',
            'responders.resource_type',
            'responders.resource_id',
            'webhook_id',
            'escalation_policy_id',
            'project_id',
            'domain_id',
            'created_at',
            'acknowledged_at',
            'resolved_at',
            'escalated_at'
        ]
    }
