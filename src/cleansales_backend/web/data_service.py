import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from re import Pattern
from typing import Any, Generic, Protocol, TypeVar

from dataclass_wizard import DatePattern
from postgrest.exceptions import APIError
from todoist_api_python.api import TodoistAPI
from todoist_api_python.models import ApiDue, Task

from cleansales_backend.domain.models.batch_aggregate import BatchAggregate
from cleansales_backend.domain.models.breed_record import BreedRecord
from cleansales_backend.domain.models.feed_record import FeedRecord
from cleansales_backend.domain.models.production_record import ProductionRecord
from cleansales_backend.domain.models.sale_record import SaleRecord
from supabase import Client

T = TypeVar("T")
logger = logging.getLogger(__name__)


@dataclass
class PaginatedData(Generic[T]):
    data: list[T]
    total: int
    has_previous: bool
    has_more: bool


class DataServiceInterface(Protocol):
    def query_batch(self, batch_name: str) -> BatchAggregate | None: ...

    def query_batches(self, start_date: str, end_date: str, chicken_breed: str) -> dict[str, BatchAggregate]: ...

    def query_batches_by_batch_name(self, batch_name: str) -> list[dict[str, Any]]: ...

    def query_sales(
        self, search_term: str | None = None, offset: int = 0, page_size: int = 100
    ) -> PaginatedData[SaleRecord]: ...

    def query_todo(self, label: str) -> list[Task]: ...

    def task_done(self, task_id: str) -> bool: ...

    def add_todo(self, form: 'TodoForm') -> Task | None: ...

    def delete_task(self, task_id: str) -> bool: ...

    def cache_info(self) -> dict[str, int]: ...

    def clear_cache(self) -> None: ...


@dataclass
class CacheResult:
    result: dict[str, BatchAggregate]
    cached_time: datetime
    hit_count: int = 0

@dataclass
class TodoForm:
    batch_name: str
    content: str
    due_date: str | None = None
    priority: int | None = None
    labels: list[str] | None = None
    description: str | None = None
    

class CachedDataService(DataServiceInterface):
    ALIVE_TIME = 5 * 60  # 5 minutes

    def __init__(self, supabase: Client, todo_service: TodoistAPI | None = None):
        self.supabase = supabase
        self.todo_service = todo_service
        self.batches: dict[str, BatchAggregate] = {}
        self._cache: dict[str, CacheResult] = {}
        self._hit_count: int = 0
        self._miss_count: int = 0

    def query_batches_by_batch_name(self, batch_name: str) -> list[dict[str, Any]]:
        query = self.supabase.table("batchaggregates").select("*").ilike("batch_name", f"%{batch_name}%").execute()
        if query.data is None:
            return []
        return query.data

    def query_batch(self, batch_name: str) -> BatchAggregate | None:
        if batch_name in self.batches:
            cached_batch = self.batches.get(batch_name)
            if cached_batch and cached_batch.cached_time + timedelta(seconds=self.ALIVE_TIME) > datetime.now():
                self._hit_count += 1
                return cached_batch
        return self.query_single_batch_db(batch_name)

    def query_batches(self, start_date: str, end_date: str, chicken_breed: str) -> dict[str, BatchAggregate]:
        query_key = f"{start_date}_{end_date}_{chicken_breed}"
        if query_key in self._cache:
            cached_result = self._cache.get(query_key)
            if cached_result and cached_result.cached_time + timedelta(seconds=self.ALIVE_TIME) > datetime.now():
                self._hit_count += 1
                return cached_result.result

        result = self.query_batches_db(start_date, end_date, chicken_breed)
        self._cache[query_key] = CacheResult(result=result, cached_time=datetime.now())
        return result

    def query_sales(
        self, search_term: str | None = None, offset: int = 0, page_size: int = 100
    ) -> PaginatedData[SaleRecord]:
        try:
            query = self.supabase.table("salerecordorm").select("*")

            if search_term and search_term.strip() != "":
                query = query.or_(f"batch_name.ilike.%{search_term}%,customer.ilike.%{search_term}%")
            total = len(query.execute().data)
            response = query.limit(page_size).offset(offset).order("sale_date", desc=True).execute()
            if response.data is None:
                return PaginatedData(data=[], total=total, has_previous=False, has_more=False)
            sale_records = [SaleRecord.model_validate(data) for data in response.data]

            return PaginatedData(
                data=sale_records,
                total=total,
                has_previous=offset > 0,
                has_more=offset + page_size < total,
            )
        except APIError as e:
            logger.error(e)
            raise APIError({"error": str(e)})
        except Exception as e:
            logger.error(e)
            raise APIError({"error": str(e)})

    def query_todo(self, label: str) -> list[Task]:
        logger.debug(f"Querying todo for label: {label}")
        if self.todo_service is None:
            return []
        try:
            response = self.todo_service.get_tasks(label=label)
            tasks = []
            while True:
                try:
                    tasks.extend(next(response))
                except StopIteration:
                    break
            logger.debug(f"Found {len(tasks)} tasks for label: {label}")
            return tasks
        except Exception as e:
            logger.error(e)
            return []

    def add_todo(self, form: TodoForm) -> Task | None:
        if self.todo_service is None:
            return None
        try:
            return self.todo_service.add_task(
                content=form.content,
                labels=[form.batch_name],
                due_date=datetime.strptime(form.due_date, "%Y-%m-%d") if form.due_date else None,
                priority=form.priority,
                description=form.description,
            )
        except Exception as e:
            logger.error(e)
            return None

    def task_done(self, task_id: str) -> bool:
        if self.todo_service is None:
            return False
        try:
            self.todo_service.complete_task(task_id)
            return True
        except Exception as e:
            logger.error(e)
            return False

    def delete_task(self, task_id: str) -> bool:
        if self.todo_service is None:
            return False
        try:
            self.todo_service.delete_task(task_id)
            return True
        except Exception as e:
            logger.error(e)
            return False

    def cache_info(self) -> dict[str, int]:
        return {
            "hit_count": self._hit_count,
            "miss_count": self._miss_count,
        }

    def clear_cache(self) -> None:
        self.batches.clear()
        self._cache.clear()
        self._hit_count = 0
        self._miss_count = 0

    def query_single_batch_db(self, batch_name: str) -> BatchAggregate | None:
        try:
            batch_response = (
                self.supabase.table("batchaggregates").select("*").eq("batch_name", batch_name).single().execute()
            )
            if batch_response.data is None:
                return None
            breed_response = self.supabase.table("breedrecordorm").select("*").eq("batch_name", batch_name).execute()
            sale_response = self.supabase.table("salerecordorm").select("*").eq("batch_name", batch_name).execute()
            feed_response = self.supabase.table("feedrecordorm").select("*").eq("batch_name", batch_name).execute()
            production_response = (
                self.supabase.table("farm_production").select("*").eq("batch_name", batch_name).execute()
            )
            breed_records = [BreedRecord.model_validate(data) for data in breed_response.data]
            sale_records = [SaleRecord.model_validate(data) for data in sale_response.data]
            feed_records = [FeedRecord.model_validate(data) for data in feed_response.data]
            production_records = [ProductionRecord.model_validate(data) for data in production_response.data]
            batch_aggregate = BatchAggregate(
                breeds=breed_records,
                sales=sale_records,
                feeds=feed_records,
                production=production_records,
            )
            self.batches[batch_name] = batch_aggregate
            self._miss_count += 1
            return batch_aggregate
        except APIError as e:
            logger.error(e)
            return None
        except Exception as e:
            logger.error(e)
            return None

    # @lru_cache(maxsize=1)
    def query_batches_db(self, start_date: str, end_date: str, chicken_breed: str) -> dict[str, BatchAggregate]:
        # time.sleep(1)
        try:
            index_response = (
                self.supabase.table("batchaggregates")
                .select("batch_name")
                .eq("chicken_breed", chicken_breed)
                .gte("final_date", start_date)
                .lte("initial_date", end_date)
                .order("initial_date")
                .execute()
            )
            # print(index_response.count)
            # if not index_response.count:
            #     return {}

            batches = [data.get("batch_name") for data in index_response.data]
            breed_response = self.supabase.table("breedrecordorm").select("*").in_("batch_name", batches).execute()
            sale_response = self.supabase.table("salerecordorm").select("*").in_("batch_name", batches).execute()
            feed_response = self.supabase.table("feedrecordorm").select("*").in_("batch_name", batches).execute()
            production_response = (
                self.supabase.table("farm_production").select("*").in_("batch_name", batches).execute()
            )
            breed_records = [BreedRecord.model_validate(data) for data in breed_response.data]
            sale_records = [SaleRecord.model_validate(data) for data in sale_response.data]
            feed_records = [FeedRecord.model_validate(data) for data in feed_response.data]
            production_records = [ProductionRecord.model_validate(data) for data in production_response.data]
            breed_dict = defaultdict(list)
            sale_dict = defaultdict(list)
            feed_dict = defaultdict(list)
            production_dict = defaultdict(list)
            for breed_record in breed_records:
                breed_dict[breed_record.batch_name].append(breed_record)
            for sale_record in sale_records:
                sale_dict[sale_record.batch_name].append(sale_record)
            for feed_record in feed_records:
                feed_dict[feed_record.batch_name].append(feed_record)
            for production_record in production_records:
                production_dict[production_record.batch_name].append(production_record)
            batchaggr = {}
            for batch_name, breeds in breed_dict.items():
                if batch_name is None:
                    continue
                batch_aggregate = BatchAggregate(
                    breeds=breeds,
                    sales=sale_dict.get(batch_name, []),
                    feeds=feed_dict.get(batch_name, []),
                    production=production_dict.get(batch_name, []),
                )
                batchaggr[batch_name] = batch_aggregate
                self.batches[batch_name] = batch_aggregate
            self._miss_count += 1
            return batchaggr
        except APIError as e:
            print(e)
            raise APIError({"error": str(e)})
        except Exception as e:
            print(e)
            raise Exception({"error": str(e)})
