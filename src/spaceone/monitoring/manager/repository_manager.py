import logging

from spaceone.core.manager import BaseManager
from spaceone.core.connector.space_connector import SpaceConnector
from spaceone.monitoring.error import *

_LOGGER = logging.getLogger(__name__)


class RepositoryManager(BaseManager):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.repo_connector: SpaceConnector = self.locator.get_connector('SpaceConnector', service='repository')

    def get_plugin(self, plugin_id, domain_id):
        return self.repo_connector.dispatch('Plugin.get', {'plugin_id': plugin_id, 'domain_id': domain_id})

    def check_plugin_version(self, plugin_id, version, domain_id):
        response = self.repo_connector.dispatch('Plugin.get_versions', {'plugin_id': plugin_id, 'domain_id': domain_id})
        versions = response.get('results', [])

        if version not in versions:
            raise ERROR_INVALID_PLUGIN_VERSION(plugin_id=plugin_id, version=version)
