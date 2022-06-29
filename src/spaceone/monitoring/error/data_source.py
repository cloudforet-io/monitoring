from spaceone.core.error import *


class ERROR_INVALID_PLUGIN_VERSION(ERROR_INVALID_ARGUMENT):
    _message = 'Plugin version is invalid. (plugin_id = {plugin_id}, version = {version})'


class ERROR_SUPPORTED_SECRETS_NOT_EXISTS(ERROR_INVALID_ARGUMENT):
    _message = 'There are no secrets that support plugins. (plugin_id = {plugin_id}, provider = {provider})'


class ERROR_RESOURCE_SECRETS_NOT_EXISTS(ERROR_INVALID_ARGUMENT):
    _message = 'There are no secrets in the resources. (resource_id = {resource_id})'


class ERROR_WRONG_PLUGIN_SETTINGS(ERROR_BASE):
    _message = "The plugin settings is incorrect. (key = {key})"


class ERROR_INVALID_PLUGIN_OPTIONS(ERROR_INTERNAL_API):
    _message = 'The options received from the plugin is invalid. (reason = {reason})'


class ERROR_DATA_SOURCE_STATE_DISABLED(ERROR_INVALID_ARGUMENT):
    _message = 'Data source state is disabled. (data_source_id = {data_source_id})'


class ERROR_REQUIRED_KEYS_NOT_EXISTS(ERROR_INVALID_ARGUMENT):
    _message = 'There are no required keys in plugins metadata. (plugin_id = {plugin_id}'
