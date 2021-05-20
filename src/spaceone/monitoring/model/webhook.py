from mongoengine import *

from spaceone.core.model.mongo_model import MongoModel


class PluginInfo(EmbeddedDocument):
    plugin_id = StringField(max_length=40)
    version = StringField(max_length=255)
    options = DictField()
    metadata = DictField()

    def to_dict(self):
        return self.to_mongo()


class Webhook(MongoModel):
    webhook_id = StringField(max_length=40)
    name = StringField(max_length=255)
    state = StringField(max_length=20, default='ENABLED', choices=('ENABLED', 'DISABLED'))
    access_key = StringField(max_length=255)
    webhook_url = StringField(max_length=255)
    capability = DictField()
    plugin_info = EmbeddedDocumentField(PluginInfo, default=None, null=True)
    tags = DictField()
    project_id = StringField(max_length=40)
    domain_id = StringField(max_length=40)
    created_at = DateTimeField(auto_now_add=True)

    meta = {
        'updatable_fields': [
            'name',
            'state',
            'repeat_count',
            'finish_condition',
            'tags'
        ],
        'minimal_fields': [
            'escalation_policy_id',
            'name',
            'is_default'
        ],
        'ordering': ['name'],
        'indexes': [
            'escalation_policy_id',
            'is_default',
            'finish_condition',
            'project_id',
            'domain_id'
        ]
    }
