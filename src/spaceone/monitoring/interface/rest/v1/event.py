import logging
from typing import Dict, Any
from fastapi import APIRouter

from spaceone.core.locator import Locator

_LOGGER = logging.getLogger(__name__)

router = APIRouter()


@router.post('/webhook/{webhook_id}/{access_key}/events')
async def webhook(webhook_id: str, access_key: str, data: Dict[Any, Any] = None):
    locator = Locator()
    event_service = locator.get_service('EventService')
    return event_service.create({
        'webhook_id': webhook_id,
        'access_key': access_key,
        'data': data or {}
    })
