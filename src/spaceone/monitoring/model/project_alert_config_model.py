from mongoengine import *

from spaceone.core.model.mongo_model import MongoModel
from spaceone.monitoring.model.escalation_policy_model import EscalationPolicy


class AlertOptions(EmbeddedDocument):
    notification_urgency = StringField(max_length=20, default='ALL', choices=('ALL', 'HIGH_ONLY'))
    recovery_mode = StringField(max_length=20, default='MANUAL', choices=('MANUAL', 'AUTO'))

    def to_dict(self):
        return self.to_mongo()


class ProjectAlertConfig(MongoModel):
    project_id = StringField(max_length=40, unique=True)
    options = EmbeddedDocumentField(AlertOptions, default=AlertOptions)
    escalation_policy = ReferenceField('EscalationPolicy', reverse_delete_rule=DENY)
    escalation_policy_id = StringField(max_length=40)
    domain_id = StringField(max_length=40)
    created_at = DateTimeField(auto_now_add=True)

    meta = {
        'updatable_fields': [
            'options',
            'escalation_policy',
            'escalation_policy_id'
        ],
        'minimal_fields': [
            'project_id',
            'options'
        ],
        'change_query_keys': {
            'user_projects': 'project_id'
        },
        'reference_query_keys': {
            'escalation_policy': EscalationPolicy
        },
        'indexes': [
            # 'project_id',
            'escalation_policy',
            'escalation_policy_id',
            'domain_id'
        ]
    }
