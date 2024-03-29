from spaceone.api.monitoring.v1 import metric_pb2
from spaceone.core.pygrpc.message_type import *

__all__ = ["MetricsInfo", "MetricDataInfo"]


def MetricDataInfo(metric_data):
    info = {
        "labels": change_list_value_type(metric_data.get("labels", [])),
        "values": change_struct_type(metric_data["values"]),
        "domain_id": metric_data["domain_id"],
    }

    return metric_pb2.MetricDataInfo(**info)


def MetricInfo(metric):
    info = {
        "key": metric["key"],
        "name": metric["name"],
    }

    if "group" in metric:
        info.update({"group": metric["group"]})

    if "unit" in metric:
        info.update({"unit": change_struct_type(metric["unit"])})

    if "metric_query" in metric:
        info.update({"metric_query": change_struct_type(metric["metric_query"])})

    return metric_pb2.MetricInfo(**info)


def MetricsInfo(metrics_info):
    info = {
        "metrics": list(map(MetricInfo, metrics_info["metrics"]))
        if metrics_info["metrics"]
        else None,
        "available_resources": change_struct_type(metrics_info["available_resources"]),
        "domain_id": metrics_info["domain_id"],
    }

    return metric_pb2.MetricsInfo(**info)
