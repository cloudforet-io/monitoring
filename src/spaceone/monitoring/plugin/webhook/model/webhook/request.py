from pydantic import BaseModel

__all__ = ["WebhookInitRequest", "WebhookVerityRequest"]


class WebhookInitRequest(BaseModel):
    options: dict


class WebhookVerityRequest(BaseModel):
    options: dict
