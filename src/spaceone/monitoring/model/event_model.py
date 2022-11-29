from mongoengine import *

from spaceone.core.model.mongo_model import MongoModel
from pydantic import BaseModel, Field
from typing import Union
from datetime import datetime


class EventResource(EmbeddedDocument):
    resource_id = StringField(default=None, null=True)
    resource_type = StringField(default=None, null=True)
    name = StringField(default=None, null=True)


class Event(MongoModel):
    event_id = StringField(max_length=40, generate_id='event', unique=True)
    event_key = StringField()
    event_type = StringField(max_length=20, default='ALERT', choices=('ALERT', 'RECOVERY', 'ERROR'))
    title = StringField()
    description = StringField(default=None, null=True)
    severity = StringField(max_length=20, default='NONE', choices=('CRITICAL', 'ERROR', 'WARNING', 'INFO',
                                                                   'NOT_AVAILABLE', 'NONE'))
    rule = StringField(default=None, null=True)
    image_url = StringField(default=None, null=True)
    resource = EmbeddedDocumentField(EventResource, default=None, null=True)
    provider = StringField(default=None, null=True)
    account = StringField(default=None, null=True)
    raw_data = DictField()
    additional_info = DictField()
    alert = ReferenceField('Alert', reverse_delete_rule=CASCADE)
    alert_id = StringField(max_length=40)
    webhook_id = StringField(max_length=40)
    project_id = StringField(max_length=40)
    domain_id = StringField(max_length=40)
    created_at = DateTimeField(auto_now_add=True)
    occurred_at = DateTimeField(default=None, null=True)

    meta = {
        'updatable_fields': [
            'alert_id',
            'project_id',
            'alert',
            'alert_id'
        ],
        'minimal_fields': [
            'event_id',
            'event_key',
            'event_type',
            'title',
            'severity',
            'alert_id'
        ],
        'change_query_keys': {
            'user_projects': 'project_id',
            'resource_id': 'resource.resource_id'
        },
        'ordering': [
            '-created_at'
        ],
        'indexes': [
            # 'event_id',
            'event_key',
            'event_type',
            'severity',
            'resource.resource_id',
            'resource.resource_type',
            'resource.name',
            'provider',
            'account',
            'alert',
            'alert_id',
            'webhook_id',
            'project_id',
            'domain_id',
            'created_at',
            'occurred_at'
        ]
    }

# Pydantic Model


class CreateEventResource(BaseModel):
    resource_id: Union[str, None] = Field(None)
    resource_type: Union[str, None] = Field(None)
    name: Union[str, None] = Field(None)


class CreateEvent(BaseModel):
    event_key: Union[str, None] = Field(None)
    event_type: Union[str, None] = Field(None)
    title: Union[str, None] = Field(None)
    description: Union[str, None] = Field(None)
    severity: Union[str, None] = Field(None)
    rule: Union[str, None] = Field(None)
    image_url: Union[str, None] = Field(None)
    resource: Union[CreateEventResource, None] = Field(None)
    additional_info: Union[dict, None] = Field(None)
    project_id: Union[str, None] = Field(None)
    occurred_at: Union[datetime, None] = Field(None)
