from typing import Optional
from datetime import datetime
from enum import Enum
from typing_extensions import TypedDict
from pydantic import BaseModel

__all__ = ['EventResponse']


class EventType(str, Enum):
    alert = 'ALERT'
    recovery = 'RECOVERY'


class Severity(str, Enum):
    critical =  'CRITICAL'
    error =  'ERROR'
    warning = 'WARNING'
    info = 'INFO'
    not_available = 'NOT_AVAILABLE'
    none = 'NONE'


class Resource(TypedDict, total=False):
    resource_id: Optional[str]
    name: Optional[str]
    resource_type: Optional[str]


class EventResponse(BaseModel):
    event_key: str
    event_type: EventType
    title: str
    description: Optional[str] = ''
    severity: Severity
    resource: Resource = None
    rule: Optional[str] = ''
    occurred_at: datetime
    additional_info: dict
    image_url: Optional[str] = ''


