from spaceone.core.error import *


class ERROR_WEBHOOK_STATE_DISABLED(ERROR_INVALID_ARGUMENT):
    _message = 'Webhook state is disabled. (webhook_id = {webhook_id})'
