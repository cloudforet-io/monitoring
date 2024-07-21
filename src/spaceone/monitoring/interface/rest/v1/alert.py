import logging
from fastapi import Request
from fastapi_utils.inferring_router import InferringRouter
from fastapi_utils.cbv import cbv
from spaceone.core.fastapi.api import BaseAPI, exception_handler
from spaceone.core.error import *
from spaceone.core import config, cache
from spaceone.monitoring.service import AlertService
from spaceone.monitoring.manager import IdentityManager
from fastapi.responses import RedirectResponse

_LOGGER = logging.getLogger(__name__)

router = InferringRouter()


@cbv(router)
class Alert(BaseAPI):
    service = "Alert"

    @router.get("/domain/{domain_id}/alert/{alert_id}/{access_key}")
    @exception_handler
    async def get_alert_info(self, domain_id: str, alert_id: str, access_key: str):
        if self._check_access_key(alert_id, access_key):
            alert_service: AlertService = self.locator.get_service("AlertService")
            try:
                return alert_service.get_alert_info(
                    {"alert_id": alert_id, "domain_id": domain_id}
                )
            except Exception as e:
                _LOGGER.error(f"Failed to get alert info: {e}", exc_info=True)
                return self._make_redirect_response(
                    alert_id, domain_id, access_key, "TIMEOUT"
                )
        else:
            return self._make_redirect_response(
                alert_id, domain_id, access_key, "TIMEOUT"
            )

    @router.get("/domain/{domain_id}/alert/{alert_id}/{access_key}/ACKNOWLEDGED")
    @exception_handler
    async def update_alert_state_get(
        self, domain_id: str, alert_id: str, access_key: str, responder: str = None
    ):
        if self._check_access_key(alert_id, access_key):
            try:
                self._update_alert_state(alert_id, domain_id, responder)
                return self._make_redirect_response(
                    alert_id, domain_id, access_key, "SUCCESS"
                )
            except Exception as e:
                _LOGGER.error(f"Failed to update alert state: {e}", exc_info=True)
                return self._make_redirect_response(
                    alert_id, domain_id, access_key, "ERROR"
                )
        else:
            return self._make_redirect_response(
                alert_id, domain_id, access_key, "TIMEOUT"
            )

    @router.post("/domain/{domain_id}/alert/{alert_id}/{access_key}/ACKNOWLEDGED")
    async def update_alert_state_post(
        self,
        domain_id: str,
        alert_id: str,
        access_key: str,
        request: Request,
    ):
        try:
            params, metadata = await self.parse_request(request)
        except Exception as e:
            _LOGGER.error(f"Failed to parse request: {e}", exc_info=True)
            params = {}

        if params.get("code") != "TIME_OUT":
            if self._check_access_key(alert_id, access_key):
                try:
                    responder = params.get("responder")
                    self._update_alert_state(alert_id, domain_id, responder)
                    return self._make_redirect_response(
                        alert_id, domain_id, access_key, "SUCCESS"
                    )
                except Exception as e:
                    _LOGGER.error(f"Failed to update alert state: {e}", exc_info=True)
                    return self._make_redirect_response(
                        alert_id, domain_id, access_key, "ERROR"
                    )
            else:
                return self._make_redirect_response(
                    alert_id, domain_id, access_key, "TIMEOUT"
                )
        else:
            return self._make_redirect_response(
                alert_id, domain_id, access_key, "TIMEOUT"
            )

    def _update_alert_state(self, alert_id: str, domain_id: str, responder: str = None):
        alert_service: AlertService = self.locator.get_service("AlertService")
        alert_service.update_state(
            {"alert_id": alert_id, "domain_id": domain_id, "responder": responder}
        )

    @cache.cacheable(key="monitoring:domain-name:{domain_id}", expire=3600)
    def _get_domain_name(self, domain_id: str) -> str:
        try:
            identity_mgr: IdentityManager = self.locator.get_manager("IdentityManager")
            domain_info = identity_mgr.get_domain_from_system(domain_id)
            return domain_info["name"]
        except Exception as e:
            _LOGGER.error(f"Failed to get domain name: {e}", exc_info=True)

        return domain_id

    @staticmethod
    def _check_access_key(alert_id: str, access_key: str):
        return cache.get(
            f"monitoring:alert:notification-callback:{alert_id}:{access_key}"
        )

    def _make_redirect_response(
        self, alert_id: str, domain_id: str, access_key: str, state: str
    ):
        console_domain = config.get_global("CONSOLE_DOMAIN")
        webhook_domain = config.get_global("WEBHOOK_DOMAIN")

        if console_domain.strip() != "" and webhook_domain.strip() != "":
            domain_name = self._get_domain_name(domain_id)

            if domain_id == domain_name:
                raise ERROR_UNKNOWN(
                    message=f"Domain is not found. (domain_id = {domain_id})"
                )

            console_domain = console_domain.format(domain_name=domain_name)
            if state == "SUCCESS":
                alert_url = f"{webhook_domain}/monitoring/v1/domain/{domain_id}/alert/{alert_id}/{access_key}"
                return RedirectResponse(
                    f"{console_domain}/alert-public-detail?alert_url={alert_url}"
                )
            else:
                return RedirectResponse(f"{console_domain}/expired-link")
        else:
            return ERROR_UNKNOWN(message="CONSOLE_DOMAIN or WEBHOOK_DOMAIN is not set.")
