import logging

from sqlalchemy.util import deprecated
from sqlmodel import Session

from ..processors import BreedRecordProcessor, SaleRecordProcessor

# from ..processors import BreedsProcessor, IProcessor, SalesProcessor
from ..shared.models import Response, SourceData

logger = logging.getLogger(__name__)


class CleanSalesService:
    _breeds_processor: BreedRecordProcessor
    _sales_processor: SaleRecordProcessor
    # _breeds_exporter: BreedSQLiteExporter
    # _sales_exporter: SaleSQLiteExporter

    def __init__(
        self,
    ) -> None:
        self._breeds_processor = BreedRecordProcessor()
        self._sales_processor = SaleRecordProcessor()
        # self._breeds_exporter = BreedSQLiteExporter()
        # self._sales_exporter = SaleSQLiteExporter()

    @deprecated(
        "1.0.0",
        message="execute_clean_sales is deprecated, use sale_processor instead",
    )
    def execute_clean_sales(
        self,
        session: Session,
        source_data: SourceData,
        check_exists: bool = True,
    ) -> Response:
        result = self._sales_processor.execute(session, source_data)
        return Response(
            status="success" if result.success else "error",
            msg=result.message,
            content=result.data,
        )

    @deprecated(
        "1.0.0",
        message="execute_clean_breeds is deprecated, use breed_processor instead",
    )
    def execute_clean_breeds(
        self,
        session: Session,
        source_data: SourceData,
        check_exists: bool = True,
    ) -> Response:
        result = self._breeds_processor.execute(session, source_data)
        return Response(
            status="success" if result.success else "error",
            msg=result.message,
            content=result.data,
        )

    # def _base_process(
    #     self,
    #     processor: IProcessor[Any],
    #     exporter: BaseSQLiteExporter[Any, Any, Any],
    #     session: Session,
    #     source_data: SourceData,
    #     pipeline_name: str,
    #     check_exists: bool = True,
    # ) -> Response:
    #     if check_exists and exporter.is_source_md5_exists_in_latest_record(
    #         session, source_data
    #     ):
    #         logger.debug(f"{pipeline_name} md5 {source_data.md5} 已存在")
    #         return Response(
    #             status="error", msg=f"{pipeline_name} 資料已存在", content={}
    #         )
    #     else:
    #         result = exporter.execute(processor.execute(source_data), session)
    #         msg: list[str] = [
    #             f"成功匯入 {pipeline_name} 資料 {result['added']} 筆資料",
    #             f"刪除 {result['deleted']} 筆資料",
    #             f"無法驗證資料 {result['unvalidated']} 筆",
    #         ]
    #         logger.info("\n".join(msg))
    #         return Response(
    #             status="success",
    #             msg="\n".join(msg),
    #             content=result,
    #         )
