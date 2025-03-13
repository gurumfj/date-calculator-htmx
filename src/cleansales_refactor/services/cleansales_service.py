import logging
from typing import Any

from sqlmodel import Session

from ..exporters import (
    BaseSQLiteExporter,
    BreedSQLiteExporter,
    SaleSQLiteExporter,
)
from ..processors import BreedsProcessor, IProcessor, SalesProcessor
from ..shared.models import Response, SourceData

logger = logging.getLogger(__name__)


class CleanSalesService:
    _breeds_processor: BreedsProcessor
    _breeds_exporter: BreedSQLiteExporter
    _sales_processor: SalesProcessor
    _sales_exporter: SaleSQLiteExporter

    def __init__(
        self,
    ) -> None:
        self._breeds_processor = BreedsProcessor()
        self._breeds_exporter = BreedSQLiteExporter()
        self._sales_processor = SalesProcessor()
        self._sales_exporter = SaleSQLiteExporter()

    def execute_clean_sales(
        self,
        session: Session,
        source_data: SourceData,
        check_exists: bool = True,
    ) -> Response:
        return self._base_process(
            self._sales_processor,
            self._sales_exporter,
            session,
            source_data,
            "販售",
            check_exists,
        )

    def execute_clean_breeds(
        self,
        session: Session,
        source_data: SourceData,
        check_exists: bool = True,
    ) -> Response:
        return self._base_process(
            self._breeds_processor,
            self._breeds_exporter,
            session,
            source_data,
            "入雛",
            check_exists,
        )

    def _base_process(
        self,
        processor: IProcessor[Any],
        exporter: BaseSQLiteExporter[Any, Any, Any],
        session: Session,
        source_data: SourceData,
        pipeline_name: str,
        check_exists: bool = True,
    ) -> Response:
        if check_exists and exporter.is_source_md5_exists_in_latest_record(
            session, source_data
        ):
            logger.debug(f"{pipeline_name} md5 {source_data.md5} 已存在")
            return Response(
                status="error", msg=f"{pipeline_name} 資料已存在", content={}
            )
        else:
            result = exporter.execute(processor.execute(source_data), session)
            msg: list[str] = [
                f"成功匯入 {pipeline_name} 資料 {result['added']} 筆資料",
                f"刪除 {result['deleted']} 筆資料",
                f"無法驗證資料 {result['unvalidated']} 筆",
            ]
            logger.info("\n".join(msg))
            return Response(
                status="success",
                msg="\n".join(msg),
                content=result,
            )
