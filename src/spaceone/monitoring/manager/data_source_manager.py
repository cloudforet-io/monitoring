import logging

from spaceone.core.manager import BaseManager

from spaceone.monitoring.model.data_source_model import DataSource

_LOGGER = logging.getLogger(__name__)


class DataSourceManager(BaseManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data_source_model: DataSource = self.locator.get_model("DataSource")

    def register_data_source(self, params: dict) -> DataSource:
        def _rollback(vo: DataSource):
            _LOGGER.info(
                f"[register_data_source._rollback] "
                f"Delete data source : {vo.name} "
                f"({vo.data_source_id})"
            )
            vo.delete()

        data_source_vo: DataSource = self.data_source_model.create(params)
        self.transaction.add_rollback(_rollback, data_source_vo)

        return data_source_vo

    def update_data_source(self, params):
        data_source_vo: DataSource = self.get_data_source(
            params["data_source_id"], params["domain_id"]
        )
        return self.update_data_source_by_vo(params, data_source_vo)

    def update_data_source_by_vo(
        self, params: dict, data_source_vo: DataSource
    ) -> DataSource:
        def _rollback(old_data: dict) -> None:
            _LOGGER.info(
                f"[update_data_source_by_vo._rollback] Revert Data : "
                f'{old_data["data_source_id"]}'
            )
            data_source_vo.update(old_data)

        self.transaction.add_rollback(_rollback, data_source_vo.to_dict())
        return data_source_vo.update(params)

    def deregister_data_source(self, data_source_id: str, domain_id: str) -> None:
        data_source_vo: DataSource = self.get_data_source(data_source_id, domain_id)
        data_source_vo.delete()

    def get_data_source(self, data_source_id: str, domain_id: str) -> DataSource:
        return self.data_source_model.get(
            data_source_id=data_source_id, domain_id=domain_id
        )

    def list_data_sources(self, query: dict) -> dict:
        return self.data_source_model.query(**query)

    def stat_data_sources(self, query: dict) -> dict:
        return self.data_source_model.stat(**query)
