from mongoengine import *

from spaceone.core.model.mongo_model import MongoModel


class PluginInfo(EmbeddedDocument):
    plugin_id = StringField(max_length=40)
    version = StringField(max_length=255)
    options = DictField()
    secret_id = StringField(max_length=40, default=None, null=True)
    provider = StringField(max_length=40, default=None, null=True)

    def to_dict(self):
        return self.to_mongo()


class DataSource(MongoModel):
    data_source_id = StringField(max_length=40, generate_id='ds', unique=True)
    name = StringField(max_length=255, unique_with='domain_id')
    state = StringField(max_length=20, default='ENABLED', choices=('ENABLED', 'DISABLED'))
    monitoring_type = StringField(max_length=20, choices=('METRIC', 'LOG'))
    provider = StringField(max_length=40, default=None, null=True)
    capability = DictField()
    plugin_info = EmbeddedDocumentField(PluginInfo, default=None, null=True)
    tags = DictField()
    domain_id = StringField(max_length=255)
    created_at = DateTimeField(auto_now_add=True)

    meta = {
        'updatable_fields': [
            'name',
            'plugin_info',
            'state',
            'tags'
        ],
        'exact_fields': [
            'data_source_id',
            'state',
            'monitoring_type',
            'provider',
            'plugin_info.plugin_id',
            'plugin_info.version',
            'plugin_info.secret_id',
            'plugin_info.provider',
            'domain_id',
        ],
        'minimal_fields': [
            'data_source_id',
            'name',
            'state',
            'monitoring_type',
            'provider'

        ],
        'ordering': [
            'name'
        ],
        'indexes': [
            'data_source_id',
            'state',
            'monitoring_type',
            'provider',
            'domain_id'
        ]
    }
