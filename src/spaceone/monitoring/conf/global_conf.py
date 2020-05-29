DATABASES = {
    'default': {
        'db': 'monitoring',
        'host': 'localhost',
        'port': 27017,
        'username': '',
        'password': ''
    }
}

CACHES = {
    'default': {},
    'local': {
        'backend': 'spaceone.core.cache.local_cache.LocalCache',
        'max_size': 128,
        'ttl': 86400
    }
}

HANDLERS = {
}

CONNECTORS = {
    'IdentityConnector': {
    },
    'InventoryConnector': {
    },
    'PluginConnector': {
    },
    'RepositoryConnector': {
    },
    'SecretConnector': {
    },
    'DataSourcePluginConnector': {
    },

}
