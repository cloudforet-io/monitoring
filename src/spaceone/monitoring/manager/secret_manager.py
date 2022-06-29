import logging

from spaceone.core.manager import BaseManager
from spaceone.core.connector.space_connector import SpaceConnector
from spaceone.monitoring.error import *

_LOGGER = logging.getLogger(__name__)


class SecretManager(BaseManager):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.secret_connector: SpaceConnector = self.locator.get_connector('SpaceConnector', service='secret')

    def get_secret_from_resource(self, resource, data_source_vo, domain_id):
        secret = None
        resource_secrets = resource.get('collection_info', {}).get('secrets', [])

        if data_source_vo.capability.get('use_resource_secret', False):
            secret_filter = {
                'provider': data_source_vo.plugin_info.provider,
                'supported_schema': data_source_vo.capability.get('supported_schema', []),
                'secrets': resource_secrets
            }
            secret = self.list_secrets_from_query(secret_filter, domain_id)[0]

        return secret

    def list_secrets(self, query, domain_id):
        return self.secret_connector.dispatch('Secret.list', {'query': query, 'domain_id': domain_id})

    def get_secret_data(self, secret_id, domain_id):
        response = self.secret_connector.dispatch('Secret.get_data', {'secret_id': secret_id, 'domain_id': domain_id})
        return response['data']

    def list_secrets_from_query(self, secret_filter, domain_id, **kwargs):
        secret_query = self._make_query(**secret_filter)
        response = self.list_secrets(secret_query, domain_id)

        if response.get('total_count', 0) == 0:
            resource_id = kwargs.get('resource_id')
            raise ERROR_RESOURCE_SECRETS_NOT_EXISTS(resource_id=resource_id)

        return response.get('results', [])

    def get_secret_data_from_plugin(self, plugin_info, capability, domain_id):
        plugin_id = plugin_info['plugin_id']
        secret_id = plugin_info.get('secret_id')
        provider = plugin_info.get('provider')

        use_resource_secret = capability.get('use_resource_secret', False)
        supported_schema = capability.get('supported_schema', [])

        self._check_plugin_secret(use_resource_secret, plugin_info)

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
    def _check_plugin_secret(use_resource_secret, plugin_info):
        secret_id = plugin_info.get('secret_id')
        provider = plugin_info.get('provider')

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
