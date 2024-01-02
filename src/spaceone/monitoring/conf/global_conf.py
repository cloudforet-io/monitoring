WEBHOOK_DOMAIN = ""
CONSOLE_DOMAIN = ""

# Service Description
TITLE = "Documentation for Monitoring Webhook"
DESCRIPTION = ""

# Database Settings
DATABASE_AUTO_CREATE_INDEX = True
DATABASES = {
    "default": {
        "db": "monitoring",
        "host": "localhost",
        "port": 27017,
        "username": "",
        "password": "",
    }
}

# Cache Settings
CACHES = {
    "default": {},
    "local": {
        "backend": "spaceone.core.cache.local_cache.LocalCache",
        "max_size": 128,
        "ttl": 300,
    },
}

# Handler Settings
HANDLERS = {
    # "authentication": [{
    #     "backend": "spaceone.core.handler.authentication_handler:SpaceONEAuthenticationHandler"
    # }],
    # "authorization": [{
    #     "backend": "spaceone.core.handler.authorization_handler:SpaceONEAuthorizationHandler"
    # }],
    # "mutation": [{
    #     "backend": "spaceone.core.handler.mutation_handler:SpaceONEMutationHandler"
    # }],
    # "event": []
}

# Log Settings
LOG = {
    "filters": {
        "masking": {
            "rules": {"Log.list": ["secret_data"], "Metric.get_data": ["secret_data"]}
        }
    }
}

# Connector Settings
CONNECTORS = {
    "SpaceConnector": {
        "backend": "spaceone.core.connector.space_connector:SpaceConnector",
        "endpoints": {
            "identity": "grpc://identity:50052",
            "inventory": "grpc://inventory:50051",
            "plugin": "grpc://plugin:50051",
            "repository": "grpc://repository:50051",
            "secret": "grpc://secret:50051",
            "notification": "grpc://notification:50051",
        },
    },
    "DataSourcePluginConnector": {},
    "WebhookPluginConnector": {},
}

# Scheduler Settings
QUEUES = {}
SCHEDULERS = {}
WORKERS = {}
TOKEN = ""
TOKEN_INFO = {}

# Job Settings
JOB_TIMEOUT = 600

# Event Settings
SAME_EVENT_TIME = 600

INSTALLED_DATA_SOURCE_PLUGINS = [
    # {
    #     'name': '',
    #     'plugin_info': {
    #         'plugin_id': '',
    #         'version': '',
    #         'options': {},
    #         'secret_data': {},
    #         'schema': '',
    #         'upgrade_mode': ''
    #     },
    #     'tags':{
    #         'description': ''
    #     }
    # }
]

MAX_CONCURRENT_WORKER = 10
MAX_REQUEST_LIMIT = 200
