from collections import defaultdict
from dataclasses import asdict
from datetime import datetime

import pandas as pd
from pydantic import ValidationError

from cleansales_refactor.models import (
    ProcessingResult,
    SaleRecord,
    SaleRecordsGroupByLocation,
    ErrorMessage,
    SaleRecordValidatorSchema,
)


class SaleRecordProcessor:
    """銷售記錄處理服務"""

    @staticmethod
    def process_data(data: pd.DataFrame) -> ProcessingResult:
        """處理資料並返回結果"""
        cleaned_records_result = SaleRecordProcessor._validate_and_clean_records(
            data
        )
        cleaned_records, errors = cleaned_records_result

        if not cleaned_records:
            return ProcessingResult([], errors)

        location_groups = SaleRecordProcessor._group_by_location(cleaned_records)
        processed_records = SaleRecordProcessor._process_groups(location_groups)
        final_groups = SaleRecordProcessor._create_final_groups(processed_records)

        return ProcessingResult(final_groups, errors)

    @staticmethod
    def _validate_and_clean_records(
        data: pd.DataFrame,
    ) -> tuple[list[SaleRecord], list[ErrorMessage]]:
        """驗證和清理記錄"""
        cleaned_records: list[SaleRecord] = []
        errors: list[ErrorMessage] = []

        for idx, row in data.iterrows():
            try:
                validated_model = SaleRecordValidatorSchema.model_validate(row)
                record = SaleRecordProcessor._validator_schema_to_dataclass(
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
    def _group_by_location(records: list[SaleRecord]) -> dict[str, list[SaleRecord]]:
        """按位置分組"""
        groups: dict[str, list[SaleRecord]] = defaultdict(list)
        for record in records:
            groups[record.location].append(record)
        return groups

    @staticmethod
    def _process_groups(groups: dict[str, list[SaleRecord]]) -> list[SaleRecord]:
        """處理分組"""
        processed_records: list[SaleRecord] = []
        for records in groups.values():
            # 預先排序記錄，避免重複排序
            sorted_records = sorted(records, key=lambda x: x.date)
            processed = SaleRecordProcessor._calculate_date_diff(sorted_records)
            processed = SaleRecordProcessor._assign_group_ids(processed)
            processed_records.extend(processed)
        return processed_records

    @staticmethod
    def _create_final_groups(
        records: list[SaleRecord],
    ) -> list[SaleRecordsGroupByLocation]:
        """創建最終分組"""
        temp_groups = defaultdict(list)
        for record in records:
            key = f"{record.location}_{record._group_id}"
            temp_groups[key].append(record)

        final_groups: list[SaleRecordsGroupByLocation] = []
        for group in temp_groups.values():
            if not group:
                continue
            min_date_record = group[0]
            max_date_record = group[-1]
            median_date = SaleRecordProcessor._calculate_date_median(
                max_date_record.date, min_date_record.date
            )
            key = SaleRecordProcessor._compose_location_string(
                max_date_record.location, median_date
            )
            final_groups.append(
                SaleRecordsGroupByLocation(location=key, sale_records=group)
            )
        return final_groups

    @staticmethod
    def _validator_schema_to_dataclass(data: SaleRecordValidatorSchema) -> SaleRecord:
        """Schema 轉換為 Dataclass"""
        new_data = data.model_copy()
        return SaleRecord(
            closed=new_data.closed,
            handler=new_data.handler,
            date=new_data.date,
            location=new_data.location,
            customer=new_data.customer,
            male_count=new_data.male_count,
            female_count=new_data.female_count,
            total_weight=new_data.total_weight,
            total_price=new_data.total_price,
            male_price=new_data.male_price,
            female_price=new_data.female_price,
            unpaid=new_data.unpaid,
        )

    @staticmethod
    def _calculate_date_diff(records: list[SaleRecord]) -> list[SaleRecord]:
        """計算銷售記錄列表中相鄰日期的差異"""
        if not records:
            return []

        result = []
        for i, record in enumerate(records):
            new_record = SaleRecord(**asdict(record))
            if i == 0:
                new_record._date_diff = 0
            else:
                diff_days = (record.date - records[i - 1].date).total_seconds() / (
                    24 * 3600
                )
                new_record._date_diff = diff_days
            result.append(new_record)

        return result

    @staticmethod
    def _assign_group_ids(
        records: list[SaleRecord], threshold_days: float = 45
    ) -> list[SaleRecord]:
        """為銷售記錄列表中的每個記錄分配組ID"""
        if not records:
            return []

        result = []
        group_id = 0

        for i, record in enumerate(records):
            new_record = SaleRecord(**asdict(record))
            if i > 0 and record._date_diff > threshold_days:
                group_id += 1
            new_record._group_id = group_id
            result.append(new_record)

        return result

    @staticmethod
    def _calculate_date_median(min_date: datetime, max_date: datetime) -> datetime:
        """計算日期中間值"""
        return min_date + (max_date - min_date) / 2

    @staticmethod
    def _compose_location_string(location: str, median_date: datetime) -> str:
        """組合場別和月份字串"""
        return (
            f"{location}{median_date.strftime('%y%m')}"
            if "'" not in location
            else location
        )
