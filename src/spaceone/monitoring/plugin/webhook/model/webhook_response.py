from typing import Optional
from pydantic import BaseModel

__all__ = ['WebhookResponse']


class WebhookResponse(BaseModel):
    metadata: Optional[dict] = {}
