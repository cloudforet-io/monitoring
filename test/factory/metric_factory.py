import factory
import time
import random


from spaceone.core import utils


class MetricFactory(factory.DictFactory):
    key = factory.LazyAttribute(lambda o: utils.generate_id("metric"))
    name = factory.LazyAttribute(lambda o: utils.random_string())
    unit = {"x": "Datetime", "y": "Count"}
    chart_type = "line"
    chart_option = {}


class MetricsFactory(factory.DictFactory):
    metrics = factory.List([factory.SubFactory(MetricFactory) for _ in range(5)])
    available_resources = {
        utils.generate_id("server"): True,
        utils.generate_id("server"): True,
        utils.generate_id("server"): True,
        utils.generate_id("server"): False,
        utils.generate_id("server"): False,
    }
    domain_id = utils.generate_id("domain")


class MetricDataFactory(factory.DictFactory):
    labels = factory.List([int(time.time()) for _ in range(10)])
    resource_values = {
        utils.generate_id("server"): [random.randint(0, 20) for _ in range(10)],
        utils.generate_id("server"): [random.randint(0, 20) for _ in range(10)],
        utils.generate_id("server"): [random.randint(0, 20) for _ in range(10)],
    }
    domain_id = utils.generate_id("domain")
