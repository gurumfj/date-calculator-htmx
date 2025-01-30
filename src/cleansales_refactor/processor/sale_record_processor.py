from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Callable, TypeAlias

import pandas as pd
from pydantic import ValidationError

from cleansales_refactor.models import (
    ErrorMessage,
    ProcessingResult,
    SaleRecord,
    # SaleRecordWithMeta,
    SaleRecordValidatorSchema,
)


@dataclass
class SaleRecordWithMeta(SaleRecord):
    date_diff: float = field(default=0)
    group_id: int = field(default=0)


GroupKey: TypeAlias = str
SalesGroups: TypeAlias = dict[GroupKey, list[SaleRecordWithMeta]]


class SalesProcessor:
    """銷售記錄處理服務"""

    @staticmethod
    def process_data(data: pd.DataFrame) -> ProcessingResult[SaleRecord]:
        """處理資料並返回結果"""
        data.sort_values(by="日期", inplace=True)

        # 驗證和清理銷售記錄
        cleaned_records, errors = SalesProcessor._validate_and_clean_records(data)

        # 如果沒有清理的記錄，返回錯誤
        if not cleaned_records:
            return ProcessingResult(
                processed_data=[],
                errors=errors,
            )

        location_groups = SalesDtoProcessor.group_by_location(cleaned_records)
        processed_groups = SaleUtil.with_dict_copy(
            location_groups, SalesProcessor._process_groups
        )

        result = SalesDtoProcessor.salesgroups_to_processingresult(
            processed_groups, errors
        )

        return result

    @staticmethod
    def _validate_and_clean_records(
        data: pd.DataFrame,
    ) -> tuple[list[SaleRecordWithMeta], list[ErrorMessage]]:
        """驗證和清理記錄"""
        cleaned_records: list[SaleRecordWithMeta] = []
        errors: list[ErrorMessage] = []

        for idx, row in data.iterrows():
            try:
                validated_model = SaleRecordValidatorSchema.model_validate(row)
                record = SalesDtoProcessor.validator_schema_to_dataclass(
                    validated_model
                )
                cleaned_records.append(record)
            except ValidationError as e:
                errors.append(
                    ErrorMessage(
                        message=str(e),
                        data=row.to_dict(),
                        extra={"row_index": idx},
                    )
                )
        return cleaned_records, errors

    @staticmethod
    def _process_groups(groups: SalesGroups) -> SalesGroups:
        """處理分組"""

        def __process_group(
            records: list[SaleRecordWithMeta],
        ) -> list[SaleRecordWithMeta]:
            result = SalesProcessor._calculate_date_diff_and_assign_group_id(records)
            result = SalesProcessor._assign_group_key_to_location(result)
            return result

        for key, records in groups.items():
            processed_records = SaleUtil.with_list_copy(records, __process_group)
            groups[key] = processed_records
        return groups

    @staticmethod
    def _calculate_date_diff_and_assign_group_id(
        records: list[SaleRecordWithMeta],
    ) -> list[SaleRecordWithMeta]:
        """計算銷售記錄列表中相鄰日期的差異"""
        if not records:
            return []

        result = []
        threshold_days = 45
        group_id = 0
        for i, record in enumerate(records):
            new_record = SaleRecordWithMeta(**asdict(record))
            new_record.date_diff = SaleUtil.assign_date_diff(
                i, record.date, records[i - 1].date
            )
            new_record.group_id = SaleUtil.assign_group_id(
                i, new_record.date_diff, threshold_days, group_id
            )
            result.append(new_record)
            group_id = new_record.group_id
        return result

    @staticmethod
    def _assign_group_key_to_location(
        group: list[SaleRecordWithMeta],
    ) -> list[SaleRecordWithMeta]:
        """創建群組鍵"""
        min_date_record = group[0]
        max_date_record = group[-1]
        median_date = SaleUtil.calculate_date_median(
            max_date_record.date, min_date_record.date
        )
        for record in group:
            key = f"{record.location}{median_date.strftime('%y%m')}"
            if "'" not in record.location:
                record.location = key
        return group


class SalesDtoProcessor:
    @staticmethod
    def validator_schema_to_dataclass(
        data: SaleRecordValidatorSchema,
    ) -> SaleRecordWithMeta:
        """Schema 轉換為 Dataclass"""
        # new_data = data.model_copy()
        return SaleRecordWithMeta(
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
    def metarecord_to_datarecord(record: SaleRecordWithMeta) -> SaleRecord:
        """MetaRecord 轉換為 Dataclass"""
        return SaleRecord(
            closed=record.closed,
            handler=record.handler,
            date=record.date,
            location=record.location,
            customer=record.customer,
            male_count=record.male_count,
            female_count=record.female_count,
            total_weight=record.total_weight,
            total_price=record.total_price,
            male_price=record.male_price,
            female_price=record.female_price,
            unpaid=record.unpaid,
        )

    @staticmethod
    def group_by_location(records: list[SaleRecordWithMeta]) -> SalesGroups:
        """按位置分組"""
        new_records = records.copy()
        return SalesDtoProcessor._group_by_field(
            new_records, lambda record: record.location
        )

    @staticmethod
    def group_by_location_and_group_id(
        records: list[SaleRecordWithMeta],
    ) -> SalesGroups:
        """按位置和群組ID分組"""
        new_records = records.copy()
        return SalesDtoProcessor._group_by_field(
            new_records, lambda record: f"{record.location}_{record.group_id}"
        )

    @staticmethod
    def salesgroups_to_processingresult(
        groups: SalesGroups, errors: list[ErrorMessage]
    ) -> ProcessingResult[SaleRecord]:
        """SalesGroups 轉換為 ProcessingResult"""
        all_records: list[SaleRecord] = []
        for records in groups.values():
            all_records.extend(
                [SalesDtoProcessor.metarecord_to_datarecord(record) for record in records]
            )
        return ProcessingResult[SaleRecord](
            processed_data=all_records,
            errors=errors,
        )

    @staticmethod
    def _group_by_field(
        records: list[SaleRecordWithMeta], field: Callable[[SaleRecordWithMeta], str]
    ) -> SalesGroups:
        groups: SalesGroups = defaultdict(list)
        for record in records:
            groups[field(record)].append(record)
        return groups


class SaleUtil:
    @staticmethod
    def with_dict_copy(
        data: dict[str, Any], callback: Callable[[dict[str, Any]], dict[str, Any]]
    ) -> dict[str, Any]:
        new_data = data.copy()
        return callback(new_data)

    @staticmethod
    def with_list_copy(
        data: list[Any], callback: Callable[[list[Any]], list[Any]]
    ) -> list[Any]:
        new_data = data.copy()
        return callback(new_data)

    @staticmethod
    def assign_date_diff(
        idx: int, current_record_date: datetime, last_record_date: datetime
    ) -> float:
        if idx == 0:
            return 0
        else:
            return (current_record_date - last_record_date).total_seconds() / (
                24 * 3600
            )

    @staticmethod
    def assign_group_id(
        idx: int, date_diff: float, threshold_days: float, group_id: int
    ) -> int:
        if idx == 0:
            return 0
        elif date_diff > threshold_days:
            return group_id + 1
        else:
            return group_id

    @staticmethod
    def calculate_date_median(min_date: datetime, max_date: datetime) -> datetime:
        """計算日期中間值"""
        return min_date + (max_date - min_date) / 2
