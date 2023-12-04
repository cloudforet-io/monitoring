from pydantic import BaseModel

__all__ = ['EventRequest']


class EventRequest(BaseModel):
    options: dict
    data: dict

