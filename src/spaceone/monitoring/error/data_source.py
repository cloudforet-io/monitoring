from spaceone.core.error import *


class ERROR_INVALID_PLUGIN_VERSION(ERROR_INVALID_ARGUMENT):
    _message = 'Plugin version is invalid. (plugin_id = {plugin_id}, version = {version})'


class ERROR_SUPPORTED_SECRETS_NOT_EXISTS(ERROR_INVALID_ARGUMENT):
    _message = 'There are no secrets that support plugins. (plugin_id = {plugin_id}, provider = {provider})'


class ERROR_RESOURCE_SECRETS_NOT_EXISTS(ERROR_INVALID_ARGUMENT):
    _message = 'There are no secrets in the resources. (resource_id = {resource_id})'


class ERROR_NOT_ALLOWED_PLUGIN_ID(ERROR_INVALID_ARGUMENT):
    _message = 'Changing plugin_id is not allowed. (old_plugin_id = {old_plugin_id}, new_plugin_id = {new_plugin_id})'


class ERROR__PLUGIN_VERSION_NOT_EXISTS(ERROR_INVALID_ARGUMENT):
    _message = 'There is no plugin version with given version info. (old_version = {old_version}, new_version = {new_version})'


class ERROR_WRONG_PLUGIN_SETTINGS(ERROR_BASE):
    _message = "The plugin settings is incorrect. (key = {key})"


class ERROR_INVALID_PLUGIN_OPTIONS(ERROR_INTERNAL_API):
    _message = 'The options received from the plugin is invalid. (reason = {reason})'


class ERROR_DATA_SOURCE_STATE_DISABLED(ERROR_INVALID_ARGUMENT):
    _message = 'Data source state is disabled. (data_source_id = {data_source_id})'
