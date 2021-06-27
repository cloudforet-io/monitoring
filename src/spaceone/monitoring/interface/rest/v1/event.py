import logging
from fastapi import APIRouter, Request, HTTPException

from spaceone.core.error import *
from spaceone.core.locator import Locator
from spaceone.monitoring.service import EventService

_LOGGER = logging.getLogger(__name__)

router = APIRouter()


@router.post('/webhook/{webhook_id}/{access_key}/events')
async def create_event(webhook_id: str, access_key: str, request: Request):
    locator = Locator()
    try:
        try:
            data = await request.json()
        except Exception as e:
            _LOGGER.debug(f'JSON Parsing Error: {e}')
            raise ERROR_UNKNOWN(message='JSON Parsing Error: Request body requires JSON format.')

        event_service: EventService = locator.get_service('EventService')
        event_service.create({
            'webhook_id': webhook_id,
            'access_key': access_key,
            'data': data or {}
        })
        return {}
    except ERROR_BASE as e:
        raise HTTPException(status_code=500, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Unknown Error: {str(e)}')
