import logging
from fastapi import APIRouter, Request, HTTPException

from spaceone.core.error import *
from spaceone.core.locator import Locator
from spaceone.monitoring.model import Alert
from spaceone.monitoring.service import AlertService

_LOGGER = logging.getLogger(__name__)

router = APIRouter()


@router.get('/alert/{alert_id}/{access_key}/{state}')
async def update_alert_state_get(alert_id: str, access_key: str, state: str):
    _update_alert_state(alert_id, access_key, state)


@router.post('/alert/{alert_id}/{access_key}/{state}')
async def update_alert_state_post(alert_id: str, access_key: str, state: str, request: Request):
    try:
        data = await request.json()
    except Exception as e:
        _LOGGER.debug(f'JSON Parsing Error: {e}')
        data = {}

    if data.get('code') != 'TIME_OUT':
        _update_alert_state(alert_id, access_key, state)


def _update_alert_state(alert_id, access_key, state):
    locator = Locator()
    try:

        alert_service: AlertService = locator.get_service('AlertService')
        alert_vo: Alert = alert_service.update_state({
            'alert_id': alert_id,
            'access_key': access_key,
            'state': state
        })

        return {
            'alert_number': alert_vo.alert_number,
            'alert_id': alert_vo.alert_id,
            'title': alert_vo.title,
            'state': alert_vo.state,
            'assignee': alert_vo.assignee,
            'urgency': alert_vo.urgency
        }

    except ERROR_BASE as e:
        raise HTTPException(status_code=500, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Unknown Error: {str(e)}')
