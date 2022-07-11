import logging
from fastapi import APIRouter, Request, HTTPException

from spaceone.core.error import *
from spaceone.core import config, cache
from spaceone.core.locator import Locator
from spaceone.monitoring.model import Alert
from spaceone.monitoring.service import AlertService
from spaceone.monitoring.manager import IdentityManager
from fastapi.responses import RedirectResponse

_LOGGER = logging.getLogger(__name__)

router = APIRouter()


@router.get('/alert/{alert_id}/{access_key}/{state}')
async def update_alert_state_get(alert_id: str, access_key: str, state: str):
    locator = Locator()

    alert_info = _update_alert_state(locator, alert_id, access_key, state)
    domain_name = _get_domain_name(locator, alert_info['domain_id'])

    return _make_redirect_response(alert_id, domain_name)


@router.post('/alert/{alert_id}/{access_key}/{state}')
async def update_alert_state_post(alert_id: str, access_key: str, state: str, request: Request):
    locator = Locator()

    try:
        data = await request.json()
    except Exception as e:
        _LOGGER.debug(f'JSON Parsing Error: {e}')
        data = {}

    if data.get('code') != 'TIME_OUT':
        alert_info = _update_alert_state(locator, alert_id, access_key, state)
        domain_name = _get_domain_name(locator, alert_info['domain_id'])

        return _make_redirect_response(alert_id, domain_name)
    else:
        raise HTTPException(status_code=403, detail='Timeout!')


def _update_alert_state(locator, alert_id, access_key, state):
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
            'urgency': alert_vo.urgency,
            'domain_id': alert_vo.domain_id
        }

    except ERROR_BASE as e:
        raise HTTPException(status_code=500, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Unknown Error: {str(e)}')


@cache.cacheable(key='domain-name:{domain_id}', expire=3600)
def _get_domain_name(locator, domain_id):
    try:
        identity_mgr: IdentityManager = locator.get_manager('IdentityManager')
        domain_info = identity_mgr.get_domain(domain_id)
        return domain_info['name']
    except Exception as e:
        _LOGGER.error(f'[_get_domain_name] Failed to get domain: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail=f'Unknown Error: {str(e)}')


def _make_redirect_response(alert_id, domain_name):
    console_domain = config.get_global('CONSOLE_DOMAIN')

    if console_domain.strip() != '':
        console_domain = console_domain.format(domain_name=domain_name)
        return RedirectResponse(f'{console_domain}/alert-manager/alert/{alert_id}')
    else:
        return None
