import factory

from spaceone.core import utils


class LogDataFactory(factory.DictFactory):

    logs = factory.List([
        {
            'name': utils.random_string(),
            'description': utils.random_string()
        },
        {
            'name': utils.random_string(),
            'description': utils.random_string()
        },
        {
            'name': utils.random_string(),
            'description': utils.random_string()
        }
    ])
    domain_id = utils.generate_id('domain')
