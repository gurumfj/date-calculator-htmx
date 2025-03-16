import json
from datetime import datetime, timedelta

from cleansales_backend import Database, settings
from cleansales_backend.domain.models import BatchAggregate
from cleansales_backend.domain.models.batch_aggregate import BatchAggregate
from cleansales_backend.processors import BreedRecordProcessor, SaleRecordProcessor
from cleansales_backend.services import QueryService

db = Database(settings.DB_PATH)
sale_repository = SaleRecordProcessor()
breed_repository = BreedRecordProcessor()
query_service = QueryService(breed_repository, sale_repository)


def get_recently_active_location(days: int = 14) -> str:
    with db.get_session() as session:
        all_aggregates: list[BatchAggregate] = query_service.get_batch_aggregates(
            session
        )
        # 將當前日期轉換為 datetime
        current_date = datetime.now() - timedelta(days=days)
        filtered_aggregates: list[BatchAggregate] = [
            x
            for x in all_aggregates
            if x.sales_trend_data.sales_period_date is not None
            and x.sales_trend_data.sales_period_date[1] > current_date
        ]
        response = [
            {
                "batch_name": x.batch_name,
                "metadata": str(x),
                "sales_summary": str(x.sales_trend_data),
            }
            for x in filtered_aggregates
        ]
        return json.dumps(response, ensure_ascii=False)


def main() -> None:
    print(get_recently_active_location())


if __name__ == "__main__":
    main()
