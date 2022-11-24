import logging
from fastapi import APIRouter, Request, HTTPException
from fastapi_utils.inferring_router import InferringRouter
from fastapi_utils.cbv import cbv
from spaceone.core.fastapi.api import BaseAPI, exception_handler
from spaceone.core.error import *
from spaceone.core.locator import Locator
from spaceone.monitoring.service import EventService

_LOGGER = logging.getLogger(__name__)

router = InferringRouter()


@cbv(router)
class Event(BaseAPI):
    @router.post('/webhook/{webhook_id}/{access_key}/events')
    async def create_event(self, webhook_id: str, access_key: str, request: Request):
        params, metadata = await self.parse_request(request)

        event_service: EventService = self.locator.get_service('EventService')
        event_service.create({
            'webhook_id': webhook_id,
            'access_key': access_key,
            'data': params or {}
        })
        return {}
