import datetime
from spaceone.api.monitoring.v1 import metric_pb2
from spaceone.core.pygrpc.message_type import *
from spaceone.core import utils

__all__ = ['MetricsInfo', 'MetricDataInfo']


def MetricDataInfo(metric_data):
    info = {
        'labels': change_list_value_type(metric_data.get('labels', [])),
        'resource_values': change_struct_type(metric_data['resource_values']),
        'domain_id': metric_data['domain_id']
    }

    return metric_pb2.MetricDataInfo(**info)


def MetricInfo(metric):
    info = {
        'key': metric['key'],
        'name': metric['name'],
        'unit': change_struct_type(metric['unit']),
        'chart_type': metric['chart_type'],
        'chart_options': change_struct_type(metric.get('chart_option', {}))
    }

    return metric_pb2.MetricInfo(**info)


def MetricsInfo(metrics_info):
    info = {
        'metrics': list(map(MetricInfo, metrics_info['metrics'])) if metrics_info['metrics'] else None,
        'available_resources': change_struct_type(metrics_info['available_resources']),
        'domain_id': metrics_info['domain_id']
    }

    return metric_pb2.MetricsInfo(**info)
