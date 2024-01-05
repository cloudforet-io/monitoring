import logging

from spaceone.core.connector.space_connector import SpaceConnector
from spaceone.core.manager import BaseManager

from spaceone.monitoring.error import *
from spaceone.monitoring.model.plugin_metadata_model import (
    MetricPluginMetadataModel,
    LogPluginMetadataModel,
)

_LOGGER = logging.getLogger(__name__)


class DataSourcePluginManager(BaseManager):
    def init_plugin(self, endpoint, options: dict, monitoring_type: str) -> dict:
        plugin_connector: SpaceConnector = self.locator.get_connector(
            "SpaceConnector", endpoint=endpoint, token="NO_TOKEN"
        )

        plugin_info = plugin_connector.dispatch("DataSource.init", {"options": options})

        _LOGGER.debug(f"[plugin_info] {plugin_info}")
        plugin_metadata = plugin_info.get("metadata", {})

        self._validate_plugin_metadata(plugin_metadata, monitoring_type)

        return plugin_metadata

    def verify_plugin(self, endpoint, options, secret_data, schema):
        plugin_connector: SpaceConnector = self.locator.get_connector(
            "SpaceConnector", endpoint=endpoint, token="NO_TOKEN"
        )

        params = {"options": options, "secret_data": secret_data, "schema": schema}

        plugin_connector.dispatch("DataSource.verify", params)

    def list_metrics(self, endpoint, schema, options, secret_data, query):
        plugin_connector: SpaceConnector = self.locator.get_connector(
            "SpaceConnector", endpoint=endpoint, token="NO_TOKEN"
        )

        params = {"options": options, "secret_data": secret_data, "query": query}

        if schema:
            params.update({"schema": schema})

        return plugin_connector.dispatch("Metric.list", params)

    def get_metric_data(self, endpoint, params):
        plugin_connector: SpaceConnector = self.locator.get_connector(
            "SpaceConnector", endpoint=endpoint, token="NO_TOKEN"
        )

        return plugin_connector.dispatch("Metric.get_data", params)

    def list_logs(
        self,
        endpoint,
        schema,
        options,
        secret_data,
        query,
        keyword,
        start,
        end,
        sort,
        limit,
    ):
        plugin_connector: SpaceConnector = self.locator.get_connector(
            "SpaceConnector", endpoint=endpoint
        )

        """
        logs_info = self.ds_plugin_mgr.list_logs(
            endpoint,
            secret.get("schema"),
            plugin_options,
            secret_data,
            query,
            params.get("keyword"),
            start,
            end,
            params.get("sort"),
            params.get("limit"),
        )
        """
        params = {
            "options": options,
            "secret_data": secret_data,
            "query": query,
            "start": start,
            "end": end,
        }

        if schema:
            params["schema"] = schema
        if keyword:
            params["keyword"] = keyword
        if sort:
            params["sort"] = sort
        if limit:
            params["limit"] = limit

        results = []
        for result in plugin_connector.dispatch("Log.list", params):
            results.extend(result.get("results", []))

        return {"results": results}

    @staticmethod
    def _validate_plugin_metadata(plugin_metadata: dict, monitoring_type: str) -> None:
        try:
            if monitoring_type == "METRIC":
                MetricPluginMetadataModel(plugin_metadata).validate()
            else:
                LogPluginMetadataModel(plugin_metadata).validate()

        except Exception as e:
            raise ERROR_INVALID_PLUGIN_OPTIONS(reason=str(e))
