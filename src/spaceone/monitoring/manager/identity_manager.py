import logging

from spaceone.core import utils
from spaceone.core.manager import BaseManager
from spaceone.monitoring.error import *
from spaceone.monitoring.connector.identity_connector import IdentityConnector

_LOGGER = logging.getLogger(__name__)

_GET_RESOURCE_METHODS = {
    'identity.Project': 'get_project',
    'identity.ServiceAccount': 'get_service_account',
}


class IdentityManager(BaseManager):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.identity_connector: IdentityConnector = self.locator.get_connector('IdentityConnector')

    def get_resource(self, resource_id, resource_type, domain_id):
        get_method = _GET_RESOURCE_METHODS[resource_type]
        return getattr(self.identity_connector, get_method)(resource_id, domain_id)

    def get_resource_key(self, resource_type, resource_info, reference_keys):
        return None
