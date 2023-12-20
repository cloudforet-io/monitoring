from pydantic import BaseModel

__all__ = ["WebhookResponse"]


class WebhookResponse(BaseModel):
    metadata: dict = {}
