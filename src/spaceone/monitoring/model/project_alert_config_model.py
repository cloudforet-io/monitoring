from mongoengine import *

from spaceone.core.model.mongo_model import MongoModel
from spaceone.monitoring.model.escalation_policy_model import EscalationPolicy


class NotificationOptions(EmbeddedDocument):
    urgency = StringField(max_length=20, default='ALL', choices=('ALL', 'HIGH_ONLY'))

    def to_dict(self):
        return self.to_mongo()


class ProjectAlertConfig(MongoModel):
    project_id = StringField(max_length=40, unique=True)
    notification_options = EmbeddedDocumentField(NotificationOptions, required=True)
    escalation_policy = ReferenceField('EscalationPolicy', reverse_delete_rule=DENY)
    escalation_policy_id = StringField(max_length=40)
    domain_id = StringField(max_length=40)
    created_at = DateTimeField(auto_now_add=True)

    meta = {
        'updatable_fields': [
            'notification_options',
            'escalation_policy',
            'escalation_policy_id'
        ],
        'minimal_fields': [
            'project_id',
            'notification_options'
        ],
        'change_query_keys': {
            'user_projects': 'project_id'
        },
        'reference_query_keys': {
            'escalation_policy': EscalationPolicy
        },
        'indexes': [
            'project_id',
            'escalation_policy',
            'escalation_policy_id',
            'domain_id'
        ]
    }
