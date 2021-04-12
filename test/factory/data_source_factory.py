import factory

from spaceone.core import utils
from spaceone.monitoring.model.data_source_model import DataSource, PluginInfo


class PluginInfoFactory(factory.mongoengine.MongoEngineFactory):

    class Meta:
        model = PluginInfo

    plugin_id = factory.LazyAttribute(lambda o: utils.generate_id('plugin'))
    version = '1.0'
    options = {}
    metadata = {
        'supported_resource_type': ['inventory.Server', 'inventory.CloudService', 'identity.ServiceAccount'],
        'supported_stat': ['AVERAGE', 'MAX', 'MIN'],
        'required_keys': ['reference.resource_id']
    }
    secret_id = None
    provider = 'aws'


class DataSourceFactory(factory.mongoengine.MongoEngineFactory):

    class Meta:
        model = DataSource

    data_source_id = factory.LazyAttribute(lambda o: utils.generate_id('ds'))
    name = factory.LazyAttribute(lambda o: utils.random_string())
    state = 'ENABLED'
    monitoring_type = 'METRIC'
    provider = 'aws'
    capability = {
        'supported_schema': ['aws_access_key'],
        'use_resource_secret': True,
        'monitoring_type': 'METRIC'
    }
    plugin_info = factory.SubFactory(PluginInfoFactory)
    tags = [
        {
            'key': 'tag_key',
            'value': 'tag_value'
        }
    ]
    domain_id = utils.generate_id('domain')
    created_at = factory.Faker('date_time')
