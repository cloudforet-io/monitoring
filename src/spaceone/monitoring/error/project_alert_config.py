from spaceone.core.error import *


class ERROR_INVALID_ESCALATION_POLICY(ERROR_INVALID_ARGUMENT):
    _message = 'Escalation policy is invalid. (escalation_policy_id = {escalation_policy_id})'


class ERROR_ALERT_FEATURE_IS_NOT_ACTIVATED(ERROR_INVALID_ARGUMENT):
    _message = 'The alert feature is not activated in the project. (project_id = {project_id})'
