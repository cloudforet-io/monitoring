from spaceone.core.error import *


class ERROR_NOT_SUPPORT_RESOURCE_TYPE(ERROR_INVALID_ARGUMENT):
    _message = (
        "Data source not support resource_type. (resource_type = {resource_type})"
    )


class ERROR_NOT_SUPPORT_METRIC_STAT(ERROR_INVALID_ARGUMENT):
    _message = "Data source not support metric stat. (stat = {stat})"


class ERROR_NOT_SUPPORT_PROVIDER_MONITORING(ERROR_INVALID_ARGUMENT):
    _message = "Data source not support provider on monitoring. (provider = {provider})"


class ERROR_NOT_MATCHING_RESOURCES(ERROR_INVALID_ARGUMENT):
    _message = "No Match found with given data. (monitoring = {monitoring})"


class ERROR_NOT_FOUND_REFERENCE_KEY(ERROR_INVALID_ARGUMENT):
    _message = (
        "Reference key not found in resource. (reference_keys = {reference_keys})"
    )


class ERROR_NOT_FOUND_REQUIRED_KEY(ERROR_INVALID_ARGUMENT):
    _message = (
        "Required key not found in plugin metadata. (data_source_id = {data_source_id})"
    )
