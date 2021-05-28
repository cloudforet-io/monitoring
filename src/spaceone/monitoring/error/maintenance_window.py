from spaceone.core.error import *


class ERROR_CLOSED_MAINTENANCE_WINDOW(ERROR_INVALID_ARGUMENT):
    _message = 'Closed maintenance window cannot be updated. (maintenance_window_id = {maintenance_window_id})'
