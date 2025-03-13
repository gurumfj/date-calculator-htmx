"""
################################################################################
# DTO 服務模組
#
# 這個模組提供了數據傳輸對象（DTO）的轉換服務，負責：
# 1. 領域模型到 API 響應模型的轉換
# 2. 數據格式化和清理
# 3. 數據驗證
#
# 主要功能：
# - 批次聚合對象轉換
# - 銷售記錄轉換
# - 統計數據轉換
################################################################################
"""

from cleansales_refactor.api.models import (
    BatchAggregateResponseModel,
)
from cleansales_refactor.domain.models import BatchAggregate


class DTOService:
    """DTO 轉換服務類"""

    @staticmethod
    def batch_aggregate_to_dto(batch: BatchAggregate) -> BatchAggregateResponseModel:
        """將批次聚合對象轉換為 DTO

        Args:
            batch (BatchAggregate): 批次聚合對象

        Returns:
            BatchAggregateResponseModel: 批次聚合 DTO
        """
        sales_trend = batch.sales_trend_data

        # 處理可能為 None 的屬性
        sales_open_close_dayage = sales_trend.sales_open_close_dayage
        cycle_date = sales_trend.cycle_date
        sales_period_date = sales_trend.sales_period_date

        return BatchAggregateResponseModel(
            batch_name=batch.batch_name,
            farm_name=batch.farm_name,
            address=batch.address,
            farmer_name=batch.farmer_name,
            total_male=batch.total_male,
            total_female=batch.total_female,
            veterinarian=batch.veterinarian,
            batch_state=batch.batch_state,
            breed_date=batch.breed_date,
            supplier=batch.supplier,
            chicken_breed=batch.chicken_breed,
            male=batch.male,
            female=batch.female,
            day_age=batch.day_age,
            week_age=batch.week_age,
            sales_percentage=sales_trend.sales_percentage,
            total_transactions=sales_trend.total_transactions,
            sales_male=sales_trend.sales_male,
            sales_female=sales_trend.sales_female,
            total_sales=sales_trend.total_sales,
            total_revenue=sales_trend.total_revenue,
            avg_weight=sales_trend.avg_weight,
            avg_male_weight=sales_trend.avg_male_weight,
            avg_female_weight=sales_trend.avg_female_weight,
            avg_male_price=sales_trend.avg_male_price,
            avg_female_price=sales_trend.avg_female_price,
            cycle_days=sales_trend.cycle_days,
            sales_duration=sales_trend.sales_duration,
            sales_open_close_dayage=sales_open_close_dayage,
            cycle_date=cycle_date,
            sales_period_date=sales_period_date,
            avg_price_weight=sales_trend.avg_price_weight,
        )

    # @staticmethod
    # def sales_record_to_dto(sale: SaleRecord) -> SalesRecordResponseModel:
    #     """將銷售記錄轉換為 DTO

    #     Args:
    #         sale (SaleRecord): 銷售記錄對象

    #     Returns:
    #         SalesRecordResponseModel: 銷售記錄 DTO
    #     """
    #     return SalesRecordResponseModel(
    #         id=sale.id,
    #         batch_name=sale.batch_name,
    #         customer_name=sale.customer_name,
    #         sale_date=sale.sale_date,
    #         quantity_male=sale.quantity_male,
    #         quantity_female=sale.quantity_female,
    #         price_male=sale.price_male,
    #         price_female=sale.price_female,
    #         total_amount=sale.total_amount,
    #         payment_status=sale.payment_status,
    #         payment_date=sale.payment_date,
    #         notes=sale.notes,
    #     )
