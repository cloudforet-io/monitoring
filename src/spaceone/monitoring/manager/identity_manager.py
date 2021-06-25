import logging

from spaceone.core.manager import BaseManager
from spaceone.core.connector.space_connector import SpaceConnector


_LOGGER = logging.getLogger(__name__)

_GET_RESOURCE_METHODS = {
    'identity.Project': 'get_project',
    'identity.ServiceAccount': 'get_service_account',
}


class IdentityManager(BaseManager):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.identity_connector: SpaceConnector = self.locator.get_connector('SpaceConnector', service='identity')

    def get_user(self, user_id, domain_id):
        return self.identity_connector.dispatch('User.get', {'user_id': user_id, 'domain_id': domain_id})

    def get_project(self, project_id, domain_id):
        return self.identity_connector.dispatch('Project.get', {'project_id': project_id, 'domain_id': domain_id})

    def get_service_account(self, service_account_id, domain_id):
        return self.identity_connector.dispatch('ServiceAccount.get', {'service_account_id': service_account_id,
                                                                       'domain_id': domain_id})

    def get_resource(self, resource_type, resource_id, domain_id):
        if resource_type == 'identity.Project':
            return self.get_project(resource_id, domain_id)
        elif resource_type == 'identity.ServiceAccount':
            return self.get_service_account(resource_id, domain_id)
