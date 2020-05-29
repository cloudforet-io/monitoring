from spaceone.core.error import *


class ERROR_NOT_SUPPORT_RESOURCE_TYPE(ERROR_INVALID_ARGUMENT):
    _message = 'Data source not support resource_type. (supported_resource_type = {supported_resource_type})'


class ERROR_NOT_FOUND_REFERENCE_KEY(ERROR_INVALID_ARGUMENT):
    _message = 'Reference key not found in resource. (reference_keys = {reference_keys})'
