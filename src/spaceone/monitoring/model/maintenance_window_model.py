from mongoengine import *

from spaceone.core.model.mongo_model import MongoModel


class MaintenanceWindow(MongoModel):
    maintenance_window_id = StringField(max_length=40, generate_id='mw', unique=True)
    title = StringField()
    state = StringField(max_length=20, default='OPEN', choices=('OPEN', 'CLOSED'))
    projects = ListField(StringField(max_length=40))
    start_time = DateTimeField()
    end_time = DateTimeField()
    tags = DictField()
    domain_id = StringField(max_length=40)
    created_by = StringField(max_length=40)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    closed_at = DateTimeField(default=None, null=True)

    meta = {
        'updatable_fields': [
            'title',
            'state',
            'projects',
            'start_time',
            'end_time',
            'tags',
            'closed_at'
        ],
        'minimal_fields': [
            'maintenance_window_id',
            'title',
            'state',
            'projects',
            'start_time',
            'end_time'
        ],
        'change_query_keys': {
            'project_id': 'projects',
            'user_projects': 'projects'
        },
        'ordering': [
            '-start_time'
        ],
        'indexes': [
            # 'maintenance_window_id',
            'state',
            'projects',
            'start_time',
            'end_time',
            'created_by',
            'domain_id'
        ]
    }
