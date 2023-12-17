from typing import List, Literal, Union
from datetime import datetime
from pydantic import BaseModel
from spaceone.core import utils

__all__ = ["EventResponse", "EventsResponse"]

EventType = Literal["ALERT", "RECOVERY"]
Severity = Literal["CRITICAL", "ERROR", "WARNING", "INFO", "NOT_AVAILABLE", "NONE"]


class Resource(BaseModel):
    resource_id: Union[str, None] = None
    name: Union[str, None] = None
    resource_type: Union[str, None] = None


class EventResponse(BaseModel):
    event_key: str
    event_type: EventType
    title: str
    description: Union[str, None] = None
    severity: Severity
    resource: Resource = {}
    rule: Union[str, None] = None
    occurred_at: datetime
    additional_info: dict
    image_url: Union[str, None] = None

    def dict(self, *args, **kwargs):
        data = super().dict(*args, **kwargs)
        data["occurred_at"] = utils.datetime_to_iso8601(data["occurred_at"])
        return data


class EventsResponse(BaseModel):
    results: List[EventResponse]
