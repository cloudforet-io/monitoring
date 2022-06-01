from mongoengine import *

from spaceone.core.model.mongo_model import MongoModel


class Note(MongoModel):
    note_id = StringField(max_length=40, generate_id='note', unique=True)
    note = StringField()
    alert_id = StringField(max_length=40)
    alert = ReferenceField('Alert', reverse_delete_rule=CASCADE)
    created_by = StringField(max_length=40)
    project_id = StringField(max_length=40)
    domain_id = StringField(max_length=40)
    created_at = DateTimeField(auto_now_add=True)

    meta = {
        'updatable_fields': [
            'note',
            'project_id'
        ],
        'minimal_fields': [
            'note_id',
            'note',
            'alert_id',
            'created_by'
        ],
        'change_query_keys': {
            'user_projects': 'project_id'
        },
        'ordering': [
            '-created_at'
        ],
        'indexes': [
            # 'note_id',
            'alert_id',
            'created_by',
            'domain_id'
        ]
    }
