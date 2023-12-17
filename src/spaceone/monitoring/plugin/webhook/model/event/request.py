from pydantic import BaseModel

__all__ = ["EventParseRequest"]


class EventParseRequest(BaseModel):
    options: dict
    data: dict
