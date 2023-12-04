from typing import List
from spaceone.monitoring.plugin.webhook.lib.server import WebhookPluginServer

app = WebhookPluginServer()

@app.route('Webhook.init')
def webhook_init(params: dict) -> dict:
    """ init plugin by options

    :param params (WebhookReauest): {
        'options': 'dict'   # Required
    }

    :return:
        WebhookResponse: {
            'metadata': 'dict'
        }
    """
    pass


@app.route('Webhook.verify')
def webhook_verify(params: dict) -> None:
    """ verifying plugin

    :param params (WebhookRequest): {
            'options': 'dict'   # Required
        }

    :return:
        None
    """
    pass


@app.route('Event.parse')
def event_parse(params: dict) -> List[dict]:
    """ Persing Event Webhook

    Args:
        params (EventRequest): {
            'options': 'dict',  # Required
            'data': 'dict'      # Required
        }

    Returns:
        List[EventResponse]
        {
            'event_key': 'str'
            'event_type': 'str'
            'title': 'str'
            'description': 'str'
            'severity': 'str'
            'resource': dict
            'rule': 'str'
            'occurred_at': 'datetime'
            'additional_info': dict
            'image_url': ''
        }
    """
    pass