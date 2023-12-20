from typing import List
from spaceone.monitoring.plugin.webhook.lib.server import WebhookPluginServer

app = WebhookPluginServer()


@app.route("Webhook.init")
def webhook_init(params: dict) -> dict:
    """init plugin by options

    Args:
        params (WebhookInitRequest): {
            'options': 'dict'      # Required
        }

    Returns:
        WebhookResponse: {
            'metadata': 'dict'
        }
    """
    pass


@app.route("Webhook.verify")
def webhook_verify(params: dict) -> None:
    """Verifying webhook plugin

    Args:
        params (WebhookVerityRequest): {
            'options': 'dict',      # Required
            'secret_data': 'dict',  # Required
            'schema': 'str',
            'domain_id': 'str'      # Required
        }

    Returns:
        None
    """
    pass


@app.route("Event.parse")
def event_parse(params: dict) -> List[dict]:
    """Parsing Event Webhook

    Args:
        params (EventRequest): {
            'options': 'dict',  # Required
            'data': 'dict'      # Required
        }

    Returns:
        List[EventResponse]
        {
            'event_key': 'str',         # Required
            'event_type': 'str',        # Required
            'title': 'str',
            'description': 'str',
            'severity': 'str',
            'resource': 'dict',
            'rule': 'str',              # Required
            'occurred_at': 'datetime',  # Required
            'additional_info': 'dict',
            'image_url': 'str'
        }
    """
    pass
