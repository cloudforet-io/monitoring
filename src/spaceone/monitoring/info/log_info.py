from spaceone.api.monitoring.v1 import log_pb2
from spaceone.core.pygrpc.message_type import *

__all__ = ['LogDataInfo']


def LogDataInfo(log_data):
    info = {
        'logs': change_list_value_type(log_data['logs']),
        'domain_id': log_data['domain_id']
    }

    return log_pb2.LogDataInfo(**info)
