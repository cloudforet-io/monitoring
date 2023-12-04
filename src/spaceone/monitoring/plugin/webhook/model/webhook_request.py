from pydantic import BaseModel

__all__ = ['WebhookRequest']


class WebhookRequest(BaseModel):
    options: dict


