from spaceone.core.error import *


class ERROR_INVALID_ESCALATION_POLICY_SCOPE(ERROR_INVALID_ARGUMENT):
    _message = 'Only global escalation policy can be set by default. (escalation_policy_id = {escalation_policy_id})'


class ERROR_DEFAULT_ESCALATION_POLICY_NOT_ALLOW_DELETION(ERROR_INVALID_ARGUMENT):
    _message = 'The default escalation policy does not allow deletion. (escalation_policy_id = {escalation_policy_id})'

