from mongoengine import *

from spaceone.core.model.mongo_model import MongoModel


class Note(MongoModel):
    note_id = StringField(max_length=40, generate_id='mw', unique=True)
    note = StringField()
    alert_id = StringField(max_length=40)
    user_id = StringField(max_length=40)
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
            'user_id'
        ],
        'indexes': [
            'note_id',
            'alert_id',
            'user_id',
            'domain_id'
        ]
    }
