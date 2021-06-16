import logging
from fastapi import APIRouter, Request

from spaceone.core.locator import Locator

_LOGGER = logging.getLogger(__name__)

router = APIRouter()


@router.post('/webhook/{webhook_id}/{access_key}/events')
async def webhook(webhook_id: str, access_key: str, request: Request):
    locator = Locator()
    data = await request.json()

    event_service = locator.get_service('EventService')
    event_service.create({
        'webhook_id': webhook_id,
        'access_key': access_key,
        'data': data or {}
    })

    return {}
