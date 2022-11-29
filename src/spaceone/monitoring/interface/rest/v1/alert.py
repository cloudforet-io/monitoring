import logging
from fastapi import Request, Body
from fastapi_utils.inferring_router import InferringRouter
from fastapi_utils.cbv import cbv
from spaceone.core.fastapi.api import BaseAPI, exception_handler
from spaceone.core.error import *
from spaceone.core import config, cache
from spaceone.monitoring.model import Alert
from spaceone.monitoring.service import AlertService
from spaceone.monitoring.manager import IdentityManager
from fastapi.responses import RedirectResponse

_LOGGER = logging.getLogger(__name__)

router = InferringRouter()


@cbv(router)
class Alert(BaseAPI):

    service = 'Alert'

    @router.get('/alert/{alert_id}/{access_key}/{state}')
    @exception_handler
    async def update_alert_state_get(self, alert_id: str, access_key: str, state: str):
        alert_info = self._update_alert_state(alert_id, access_key, state)
        domain_name = self._get_domain_name(alert_info['domain_id'])

        return self._make_redirect_response(alert_id, domain_name)

    @router.post('/alert/{alert_id}/{access_key}/{state}')
    async def update_alert_state_post(self, alert_id: str, access_key: str, state: str, request: Request):
        params, metadata = await self.parse_request(request)

        if params.get('code') != 'TIME_OUT':
            self._update_alert_state(alert_id, access_key, state)

            return {
                'detail': f'Alert({alert_id}) state was changed.'
            }
        else:
            raise ERROR_REQUEST_TIMEOUT()

    def _update_alert_state(self, alert_id, access_key, state):
        alert_service: AlertService = self.locator.get_service('AlertService')

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

    @cache.cacheable(key='domain-name:{domain_id}', expire=3600)
    def _get_domain_name(self, domain_id):
        identity_mgr: IdentityManager = self.locator.get_manager('IdentityManager')
        domain_info = identity_mgr.get_domain(domain_id)
        return domain_info['name']

    @staticmethod
    def _make_redirect_response(alert_id, domain_name):
        console_domain = config.get_global('CONSOLE_DOMAIN')

        if console_domain.strip() != '':
            console_domain = console_domain.format(domain_name=domain_name)
            return RedirectResponse(f'{console_domain}/alert-manager/alert/{alert_id}')
        else:
            return None
