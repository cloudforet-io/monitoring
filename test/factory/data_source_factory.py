import factory

from spaceone.core import utils
from spaceone.monitoring.model.data_source_model import DataSource, PluginInfo


class PluginInfoFactory(factory.mongoengine.MongoEngineFactory):
    class Meta:
        model = PluginInfo

    plugin_id = factory.LazyAttribute(lambda o: utils.generate_id("plugin"))
    version = "1.0"
    options = {}
    metadata = {
        "supported_resource_type": ["inventory.CloudService"],
        "supported_stat": ["AVERAGE", "MAX", "MIN"],
        "required_keys": ["data.cloudwatch"],
    }
    secret_id = None
    provider = "aws"
    upgrade_mode = "AUTO"


class DataSourceFactory(factory.mongoengine.MongoEngineFactory):
    class Meta:
        model = DataSource

    data_source_id = factory.LazyAttribute(lambda o: utils.generate_id("ds"))
    name = factory.LazyAttribute(lambda o: utils.random_string())
    state = "ENABLED"
    monitoring_type = "METRIC"
    provider = "aws"
    capability = {
        "supported_schema": ["aws_access_key"],
        "use_resource_secret": True,
        "monitoring_type": "METRIC",
    }
    plugin_info = factory.SubFactory(PluginInfoFactory)
    tags = {"tag_key": "tag_value"}
    domain_id = utils.generate_id("domain")
    created_at = factory.Faker("date_time")
