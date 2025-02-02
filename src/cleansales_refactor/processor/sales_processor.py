import logging
from dataclasses import dataclass, field, replace
from datetime import datetime
from functools import reduce
from typing import Any, Callable, Hashable, TypeAlias, TypeVar

import pandas as pd

from ..models import (
    ErrorMessage,
    ProcessingResult,
    SaleRecord,
    SaleRecordValidatorSchema,
)
from .processor_interface import IProcessor

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@dataclass(frozen=True)
class SaleRecordUpdate(SaleRecord):
    """不可變的銷售記錄更新，負責所有數據轉換"""

    @classmethod
    def create_from(
        cls, data: dict[str, Any] | SaleRecord | SaleRecordValidatorSchema
    ) -> "SaleRecordUpdate":
        """從各種來源創建更新物件"""
        if isinstance(data, SaleRecordValidatorSchema):
            return cls(**data.model_dump())
        if isinstance(data, SaleRecord):
            return cls(**data.__dict__)
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})

    def with_updates(self, **updates: Any) -> "SaleRecordUpdate":
        """通用的更新方法"""
        return replace(self, **updates)


# Type Aliases
GroupID: TypeAlias = int
PreRecords: TypeAlias = tuple[SaleRecordUpdate, ...]
GroupedRecords: TypeAlias = tuple[SaleRecordUpdate, ...]
ProcessedRecords: TypeAlias = tuple[SaleRecordUpdate, ...]
# SeriesRow: TypeAlias = pd.Series  # type: ignore

T = TypeVar("T")
R = TypeVar("R")


@dataclass(frozen=True)
class ProcessingState:
    """不可變的處理狀態"""

    processed_records: ProcessedRecords = field(default_factory=tuple)
    grouped_records: GroupedRecords = field(default_factory=tuple)
    group_id: GroupID = 0
    cleaned_records: PreRecords = field(default_factory=tuple)

    def add_to_group(self, record: SaleRecordUpdate) -> "ProcessingState":
        """將記錄加入群組"""
        return replace(
            self,
            grouped_records=(*self.grouped_records, record),
        )

    def process_current_group(
        self, processed_group: ProcessedRecords
    ) -> "ProcessingState":
        """處理當前群組"""
        return replace(
            self,
            processed_records=(*self.processed_records, *processed_group),
            grouped_records=(),
            group_id=self.group_id + 1,
        )


class SaleUtil:
    """不可變的工具類"""

    @staticmethod
    def map_tuple(
        data: tuple[T, ...],
        func: Callable[[T], R],
    ) -> tuple[R, ...]:
        """映射元組的每個元素"""
        return tuple(func(item) for item in data)

    @staticmethod
    def filter_tuple(
        data: tuple[T, ...],
        predicate: Callable[[T], bool],
    ) -> tuple[T, ...]:
        """過濾元組的元素"""
        return tuple(item for item in data if predicate(item))

    @staticmethod
    def reduce_tuple(
        data: tuple[T, ...],
        func: Callable[[R, T], R],
        initial: R,
    ) -> R:
        """歸納元組的元素"""
        return reduce(func, data, initial)

    @staticmethod
    def catch_error(
        callback: Callable[[], T],
        error_callback: Callable[[Exception], T],
    ) -> T:
        """安全的錯誤處理"""
        try:
            return callback()
        except Exception as e:
            return error_callback(e)


class SalesProcessor(IProcessor[SaleRecord]):
    """銷售記錄處理服務"""

    @staticmethod
    def process_data(data: pd.DataFrame) -> ProcessingResult[SaleRecord]:
        """處理資料並返回結果"""

        # 驗證和清理銷售記錄
        cleaned_records, errors = SalesProcessor._validate_and_clean_records(data)

        # 初始化不可變狀態
        initial_state = ProcessingState(cleaned_records=tuple(cleaned_records))

        # 使用 reduce 處理所有記錄
        final_state = reduce(
            SalesProcessor._process_group_and_assign_keys,
            enumerate(cleaned_records),
            initial_state,
        )

        logger.info(f"處理完成，共產生 {len(final_state.processed_records)} 筆記錄")
        return ProcessingResult(
            processed_data=list(final_state.processed_records),  # 轉回 list
            errors=errors,
        )

    @staticmethod
    def _should_create_new_group(
        current: SaleRecordUpdate | None, next_record: SaleRecordUpdate | None
    ) -> bool:
        def over_threshold(date: datetime, next_date: datetime) -> bool:
            return abs((next_date - date).days) > 45

        if current is None or next_record is None:
            return False
        if current.location != next_record.location:
            logger.debug(f"位置改變: {current.location} -> {next_record.location}")
            return True
        if over_threshold(next_record.date, current.date):
            logger.debug(f"日期差異超過閾值: {current.date} -> {next_record.date}")
            return True
        return False

    @staticmethod
    def _process_group_and_assign_keys(
        state: ProcessingState,
        record_with_idx: tuple[int, SaleRecordUpdate | None],
    ) -> ProcessingState:
        idx, record = record_with_idx

        if record is None:
            return state

        # 將記錄加入當前群組
        new_state = state.add_to_group(record)

        # 檢查是否需要處理並清空當前群組
        should_process_group = (
            idx == len(state.cleaned_records) - 1  # 最後一筆
            or (
                idx < len(state.cleaned_records) - 1
                and SalesProcessor._should_create_new_group(
                    record, state.cleaned_records[idx + 1]
                )
            )
        )

        if should_process_group:
            # 處理當前群組
            processed_group = tuple(
                SalesProcessor._assign_group_key_to_location(
                    new_state.grouped_records,
                )
            )
            return new_state.process_current_group(processed_group)

        return new_state

    @staticmethod
    def _validate_and_clean_records(
        data: pd.DataFrame,
    ) -> tuple[PreRecords, list[ErrorMessage]]:
        sorted_data = data.sort_values(by=["場別", "日期"])

        def process_row(
            acc: tuple[PreRecords, list[ErrorMessage]],
            row_with_idx: tuple[Hashable, pd.Series],  # type: ignore
        ) -> tuple[PreRecords, list[ErrorMessage]]:
            records, errors = acc
            idx, row = row_with_idx

            try:
                model = SaleRecordValidatorSchema.model_validate(row)
                record = SaleRecordUpdate.create_from(model)
                return (*records, record), errors
            except Exception as e:
                error = ErrorMessage(
                    message=str(e),
                    data=row.to_dict(),
                    extra={"row_index": idx},
                )
                logger.warning(f"資料驗證失敗: {error}")
                return records, [*errors, error]

        initial_result: tuple[PreRecords, list[ErrorMessage]] = ((), [])
        cleaned_records, errors = reduce(
            process_row,
            sorted_data.iterrows(),
            initial_result,
        )

        logger.info(f"資料清理完成，共 {len(cleaned_records)} 筆有效記錄")
        if errors:
            logger.warning(f"發現 {len(errors)} 筆錯誤記錄")
        return cleaned_records, errors

    @staticmethod
    def _assign_group_key_to_location(
        group: tuple[SaleRecordUpdate, ...],
    ) -> tuple[SaleRecordUpdate, ...]:
        """創建群組鍵值"""
        if not group:
            return ()

        min_date_record = group[0]
        max_date_record = group[-1]
        median_date = SalesProcessor._calculate_date_median(
            max_date_record.date, min_date_record.date
        )

        def update_location(record: SaleRecordUpdate) -> SaleRecordUpdate:
            if "'" in record.location:
                return record

            key = f"{record.location}{median_date.strftime('%y%m')}"
            # logger.debug(f"生成位置鍵值: {key} (群組大小: {len(group)})")
            return record.with_updates(location=key)

        return SaleUtil.map_tuple(group, update_location)

    @staticmethod
    def _calculate_date_median(min_date: datetime, max_date: datetime) -> datetime:
        """計算日期中間值"""
        return min_date + (max_date - min_date) / 2
