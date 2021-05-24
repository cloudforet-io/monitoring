from spaceone.core.error import *


class ERROR_SAME_RESPONDER_ALREADY_EXISTS(ERROR_INVALID_ARGUMENT):
    _message = 'The same responder already exists. (resource_type = {resource_type}, resource_id = {resource_id})'


class ERROR_RESPONDER_NOT_EXIST(ERROR_INVALID_ARGUMENT):
    _message = 'Responder does not exist. (resource_type = {resource_type}, resource_id = {resource_id})'

