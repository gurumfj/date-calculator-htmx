from collections import defaultdict
from datetime import datetime
from functools import reduce
from typing import Any, Callable, Hashable, TypeAlias, TypeVar

import pandas as pd

from cleansales_refactor.models import (
    ErrorMessage,
    ProcessingResult,
    SaleRecord,
    SaleRecordValidatorSchema,
)

GroupKey: TypeAlias = str
SalesGroups: TypeAlias = dict[GroupKey, list[SaleRecord]]
T = TypeVar("T")
R = TypeVar("R")


class SalesProcessor:
    """銷售記錄處理服務"""

    @staticmethod
    def process_data(data: pd.DataFrame) -> ProcessingResult[SaleRecord]:
        """處理資料並返回結果"""

        # 驗證和清理銷售記錄
        cleaned_records, errors = SalesProcessor._validate_and_clean_records(data)

        def over_threshold(date: datetime, next_date: datetime) -> bool:
            return abs((next_date - date).days) > 45

        sale_groups: SalesGroups = defaultdict(list)
        group_id = 0

        # 處理所有記錄，包含最後一筆
        for idx, record in enumerate(cleaned_records):
            if record is None:
                continue

            sale_groups[f"{group_id}"].append(record)

            # 如果不是最後一筆，檢查是否需要更新 group_id
            if idx < len(cleaned_records) - 1:
                next_record = cleaned_records[idx + 1]
                if next_record is None:
                    continue

                if next_record.location != record.location:
                    print(
                        f"change location: {next_record.location} - {next_record.date}"
                    )
                    group_id += 1
                    continue

                if over_threshold(next_record.date, record.date):
                    print(f"over threshold: {next_record.date} - {record.date}")
                    group_id += 1

        new_records: list[SaleRecord] = reduce(
            lambda acc, group: acc
            + SalesProcessor._assign_group_key_to_location(group),
            sale_groups.values(),
            [],
        )
        print(f"count of new_records: {len(new_records)}")
        return ProcessingResult(
            processed_data=new_records,
            errors=errors,
        )

    @staticmethod
    def _validate_and_clean_records(
        data: pd.DataFrame,
    ) -> tuple[list[SaleRecord], list[ErrorMessage]]:
        # 創建排序後的副本，而不是修改原始資料
        sorted_data = data.sort_values(by=["場別", "日期"])

        def process_row(
            idx: Hashable,
            row: pd.Series[Any],
        ) -> tuple[list[SaleRecord], list[ErrorMessage]]:
            try:
                record = SalesProcessor._validator_schema_to_dataclass(
                    SaleRecordValidatorSchema.model_validate(row)
                )
                return [record], []
            except Exception as e:
                error = ErrorMessage(
                    message=str(e),
                    data=row.to_dict(),
                    extra={"row_index": idx},
                )
                return [], [error]

        # 直接使用 reduce 處理每一行的結果
        initial_result: tuple[list[SaleRecord], list[ErrorMessage]] = ([], [])
        cleaned_records, errors = reduce(
            lambda acc, row_with_idx: (
                acc[0] + process_row(row_with_idx[0], row_with_idx[1])[0],
                acc[1] + process_row(row_with_idx[0], row_with_idx[1])[1],
            ),
            sorted_data.iterrows(),
            initial_result,
        )

        print(f"count of cleaned_records: {len(cleaned_records)}")
        print(f"errors: {errors}")
        return cleaned_records, errors

    @staticmethod
    def _assign_group_key_to_location(
        group: list[SaleRecord],
    ) -> list[SaleRecord]:
        """創建群組鍵"""
        min_date_record = group[0]
        max_date_record = group[-1]
        median_date = SalesProcessor._calculate_date_median(
            max_date_record.date, min_date_record.date
        )

        def replace_location_with_key_and_return_datarecord(
            record: SaleRecord,
        ) -> SaleRecord:
            key = f"{record.location}{median_date.strftime('%y%m')}"
            if "'" not in record.location:
                data_dict = record.__dict__.copy()
                data_dict.pop("location")
                return SaleRecord(
                    location=key,
                    **data_dict,
                )
            return record

        return SaleUtil.with_list_copy(
            group,
            lambda records: SaleUtil.for_each_list(
                records,
                replace_location_with_key_and_return_datarecord,
            ),
        )

    @staticmethod
    def _validator_schema_to_dataclass(
        data: SaleRecordValidatorSchema,
    ) -> SaleRecord:
        """Schema 轉換為 Dataclass"""
        return SaleRecord(
            closed=data.closed,
            handler=data.handler,
            date=data.date,
            location=data.location,
            customer=data.customer,
            male_count=data.male_count,
            female_count=data.female_count,
            total_weight=data.total_weight,
            total_price=data.total_price,
            male_price=data.male_price,
            female_price=data.female_price,
            unpaid=data.unpaid,
        )

    @staticmethod
    def _calculate_date_median(min_date: datetime, max_date: datetime) -> datetime:
        """計算日期中間值"""
        return min_date + (max_date - min_date) / 2


class SaleUtil:
    # @staticmethod
    # def with_dict_copy(
    #     data: dict[str, Any], callback: Callable[[dict[str, Any]], dict[str, Any]]
    # ) -> dict[str, Any]:
    #     new_data = data.copy()
    #     return callback(new_data)

    @staticmethod
    def with_list_copy(
        data: list[Any], callback: Callable[[list[Any]], list[Any]]
    ) -> list[Any]:
        new_data = data.copy()
        return callback(new_data)

    @staticmethod
    def for_each_list(
        records: list[Any],
        callback: Callable[[Any], Any],
    ) -> list[Any]:
        result = []
        for record in records:
            result.append(callback(record))
        return result

    @staticmethod
    def catch_error(
        callback: Callable[[], Any],
        error_callback: Callable[[Exception], Any],
    ) -> Any:
        try:
            return callback()
        except Exception as e:
            return error_callback(e)
