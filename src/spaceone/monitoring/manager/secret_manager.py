import logging

from spaceone.core.manager import BaseManager
from spaceone.core.connector.space_connector import SpaceConnector
from spaceone.monitoring.error import *

_LOGGER = logging.getLogger(__name__)


class SecretManager(BaseManager):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.secret_connector: SpaceConnector = self.locator.get_connector('SpaceConnector', service='secret')

    def list_secrets(self, query, domain_id):
        return self.secret_connector.dispatch('Secret.list', {'query': query, 'domain_id': domain_id})

    def get_secret_data(self, secret_id, domain_id):
        response = self.secret_connector.dispatch('Secret.get_data', {'secret_id': secret_id, 'domain_id': domain_id})
        return response['data']

    def get_plugin_secret_data(self, secret_id, supported_schema, domain_id):
        secret_query = self._make_query(supported_schema=supported_schema, secret_id=secret_id)
        response = self.list_secrets(secret_query, domain_id)

        if response.get('total_count', 0) == 0:
            raise ERROR_NOT_FOUND(key='plugin_info.secret_id', value=secret_id)

        return self.get_secret_data(secret_id, domain_id)

    def get_resource_secret_data(self, resource_id, secret_filter, domain_id):
        secret_query = self._make_query(**secret_filter)

        response = self.list_secrets(secret_query, domain_id)

        if response.get('total_count', 0) == 0:
            raise ERROR_RESOURCE_SECRETS_NOT_EXISTS(resource_id=resource_id)

        result = response['results'][0]
        secret_id = result['secret_id']
        schema = result.get('schema')

        return self.get_secret_data(secret_id, domain_id), schema

    def get_plugin_secret(self, plugin_id, secret_id, provider, capability, domain_id):
        use_resource_secret = capability.get('use_resource_secret', False)
        supported_schema = capability.get('supported_schema', [])

        self._check_plugin_secret(use_resource_secret, secret_id, provider)

        if use_resource_secret:
            secret_query = self._make_query(supported_schema=supported_schema, provider=provider)
        else:
            secret_query = self._make_query(supported_schema=supported_schema, secret_id=secret_id)

        response = self.list_secrets(secret_query, domain_id)

        if response.get('total_count', 0) == 0:
            if use_resource_secret:
                raise ERROR_SUPPORTED_SECRETS_NOT_EXISTS(plugin_id=plugin_id, provider=provider)
            else:
                raise ERROR_NOT_FOUND(key='plugin_info.secret_id', value=secret_id)

        result = response['results'][0]
        secret_id = result['secret_id']
        schema = result.get('schema')

        return self.get_secret_data(secret_id, domain_id), schema

    @staticmethod
    def _check_plugin_secret(use_resource_secret, secret_id, provider):
        if use_resource_secret:
            if provider is None:
                raise ERROR_REQUIRED_PARAMETER(key='plugin_info.provider')
        else:
            if secret_id is None:
                raise ERROR_REQUIRED_PARAMETER(key='plugin_info.secret_id')

    @staticmethod
    def _make_query(**secret_filter):
        supported_schema = secret_filter.get('supported_schema')
        secret_id = secret_filter.get('secret_id')
        service_account_id = secret_filter.get('service_account_id')
        project_id = secret_filter.get('project_id')
        provider = secret_filter.get('provider')
        secrets = secret_filter.get('secrets')

        query = {
            'filter': []
        }

        if supported_schema:
            query['filter'].append({
                'k': 'schema',
                'v': supported_schema,
                'o': 'in'
            })

        if secret_id:
            query['filter'].append({
                'k': 'secret_id',
                'v': secret_id,
                'o': 'eq'
            })

        if provider:
            query['filter'].append({
                'k': 'provider',
                'v': provider,
                'o': 'eq'
            })

        if service_account_id:
            query['filter'].append({
                'k': 'service_account_id',
                'v': service_account_id,
                'o': 'eq'
            })

        if project_id:
            query['filter'].append({
                'k': 'project_id',
                'v': project_id,
                'o': 'eq'
            })

        if secrets:
            query['filter'].append({
                'k': 'secret_id',
                'v': secrets,
                'o': 'in'
            })

        return query
