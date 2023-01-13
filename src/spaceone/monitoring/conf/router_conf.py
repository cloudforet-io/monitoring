ROUTER = [
    {
        'router_path': 'spaceone.monitoring.interface.rest.v1.alert:router',
        'router_options': {
            'prefix': '/monitoring/v1',
        }
    },
    {
        'router_path': 'spaceone.monitoring.interface.rest.v1.event:router',
        'router_options': {
            'prefix': '/monitoring/v1',
        }
    },
]