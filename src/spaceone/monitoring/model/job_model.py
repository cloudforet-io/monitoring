from mongoengine import *

from spaceone.core.model.mongo_model import MongoModel


class Error(EmbeddedDocument):
    error_code = StringField(max_length=128)
    message = StringField(max_length=2048)


class Job(MongoModel):
    job_id = StringField(max_length=40, generate_id='job', unique=True)
    domain_id = StringField(max_length=40, required=True)
    status = StringField(max_length=20, default='IN_PROGRESS', choices=('IN_PROGRESS', 'SUCCESS', 'ERROR', 'TIMEOUT'))
    errors = ListField(EmbeddedDocumentField(Error, default=None, null=True))
    total_tasks = IntField(default=0)
    remained_tasks = IntField(default=0)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    finished_at = DateTimeField(default=None, null=True)

    meta = {
        'updatable_fields': [
            'status',
            'errors',
            'total_tasks',
            'remained_tasks',
            'finished_at'
        ],
        'ordering': [
            '-created_at'
        ],
        'indexes': [
            # 'job_id',
            'domain_id',
            'status',
            'total_tasks',
            'remained_tasks',
            'created_at'
        ]
    }
