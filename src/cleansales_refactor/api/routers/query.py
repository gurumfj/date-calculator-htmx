import logging
import traceback

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from cleansales_refactor.domain.models import BatchAggregate, SaleRecord
from cleansales_refactor.services import QueryService

from .. import get_session
from ..models import (
    BatchAggregateResponseModel,
    SalesRecordResponseModel,
)

logger = logging.getLogger(__name__)
query_service = QueryService()
router = APIRouter(prefix="/api", tags=["api"])


@router.get("/not-completed", response_model=list[BatchAggregateResponseModel])
async def get_breeding_data(
    session: Session = Depends(get_session),
) -> list[BatchAggregateResponseModel]:
    """取得未結案的入雛批次資料"""
    try:
        query_result = query_service.get_breeds_is_not_completed(session)
        return [DTOService.batch_aggregate_to_dto(q) for q in query_result]
    except Exception as e:
        error_msg = f"取得未結案的入雛批次資料時發生錯誤: {str(e)}\n"
        error_msg += f"錯誤類型: {type(e).__name__}\n"
        error_msg += f"堆疊追蹤:\n{traceback.format_exc()}"
        logger.error(error_msg)
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "type": type(e).__name__,
                "traceback": traceback.format_exc(),
            },
        )


@router.get("/q/{batch_name}", response_model=list[BatchAggregateResponseModel])
async def get_sales_by_batch_name(
    batch_name: str,
    session: Session = Depends(get_session),
) -> list[BatchAggregateResponseModel]:
    query_result = query_service.get_breed_by_batch_name(session, batch_name)
    return [DTOService.batch_aggregate_to_dto(q) for q in query_result]


@router.get("/sales", response_model=list[SalesRecordResponseModel])
async def get_sales_data(
    limit: int = Query(default=100, ge=1, le=300),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
) -> list[SalesRecordResponseModel]:
    try:
        query_result = query_service.get_sales_data(session, limit, offset)
        return [DTOService.sales_record_to_dto(sale) for sale in query_result]
    except Exception as e:
        error_msg = f"取得銷售資料時發生錯誤: {str(e)}\n"
        error_msg += f"錯誤類型: {type(e).__name__}\n"
        error_msg += f"堆疊追蹤:\n{traceback.format_exc()}"
        logger.error(error_msg)
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "type": type(e).__name__,
                "traceback": traceback.format_exc(),
            },
        )


class DTOService:
    @staticmethod
    def batch_aggregate_to_dto(
        data_model: BatchAggregate,
    ) -> BatchAggregateResponseModel:
        return BatchAggregateResponseModel(
            batch_name=data_model.batch_name,
            farm_name=data_model.farm_name,
            address=data_model.address,
            farmer_name=data_model.farmer_name,
            total_male=data_model.total_male,
            total_female=data_model.total_female,
            veterinarian=data_model.veterinarian,
            batch_state=data_model.batch_state,
            breed_date=data_model.breed_date,
            supplier=data_model.supplier,
            chicken_breed=data_model.chicken_breed,
            male=data_model.male,
            female=data_model.female,
            day_age=data_model.day_age,
            week_age=data_model.week_age,
            sales_male=data_model.sales_male,
            sales_female=data_model.sales_female,
            total_sales=data_model.total_sales,
            sales_percentage=data_model.sales_percentage,
        )

    @staticmethod
    def sales_record_to_dto(data_model: SaleRecord) -> SalesRecordResponseModel:
        return SalesRecordResponseModel(
            closed=data_model.closed,
            handler=data_model.handler,
            date=data_model.date,
            location=data_model.location,
            customer=data_model.customer,
            male_count=data_model.male_count,
            female_count=data_model.female_count,
            total_weight=data_model.total_weight,
            total_price=data_model.total_price,
            male_price=data_model.male_price,
            female_price=data_model.female_price,
            unpaid=data_model.unpaid,
        )
