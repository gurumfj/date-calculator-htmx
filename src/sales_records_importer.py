import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import TypeAlias

import pandas as pd
from pydantic import ValidationError

from cleansales_refactor.validator_schema.error import ErrorMessage
from cleansales_refactor.validator_schema.sales_schema import SaleRecordValidatorSchema

logger = logging.getLogger(__name__)

Location: TypeAlias = str


@dataclass
class SaleRecord:
    closed: str | None
    handler: str | None
    date: datetime
    location: str
    customer: str
    male_count: int
    female_count: int
    total_weight: float | None
    total_price: float | None
    male_price: float | None
    female_price: float | None
    unpaid: str | None
    _date_diff: float = field(default=0, init=False)
    _group_id: int = field(default=0, init=False)


@dataclass
class SaleRecordsGroupByLocation:
    location: str
    sale_records: list[SaleRecord]


class SaleRecordRawDataImporter:
    _errors: list[ErrorMessage]
    _final_grouped_data: list[SaleRecordsGroupByLocation]

    def __init__(self) -> None:
        self._errors: list[ErrorMessage] = []
        self._final_grouped_data = []

    def execute(self, data: pd.DataFrame) -> None:
        """[Action] 執行資料處理，修改內部狀態 _errors 和 _final_grouped_data"""
        sorted_data = data.sort_values(by=["日期", "場別"])
        cleaned_records: list[SaleRecord] = []
        for idx, row in sorted_data.iterrows():
            try:
                validated_model = SaleRecordValidatorSchema.model_validate(row)
                record = self._validator_schema_to_dataclass(validated_model)
                cleaned_records.append(record)
            except ValidationError as e:
                self._errors.append(
                    ErrorMessage(
                        message=str(e),
                        data=row.to_dict(),
                        extra={"row_index": idx},
                    )
                )

        location_groups: dict[str, list[SaleRecord]] = defaultdict(list)
        for record in cleaned_records:
            location_groups[record.location].append(record)

        processed_records: list[SaleRecord] = []
        for _, group in location_groups.items():
            group = self._calculate_date_diff(group)
            group = self._assign_group_ids(group)
            processed_records.extend(group)

        final_groups = defaultdict(list)
        for record in processed_records:
            key = f"{record.location}_{record._group_id}"
            final_groups[key].append(record)

        for _, group in final_groups.items():
            min_date_record = group[0]
            max_date_record = group[-1]
            median_date = self._calculate_date_median(
                max_date_record.date, min_date_record.date
            )
            key = self._compose_location_string(max_date_record.location, median_date)
            self._final_grouped_data.append(
                SaleRecordsGroupByLocation(location=key, sale_records=group)
            )

    def to_excel(self, file_path: str) -> None:
        """[Action] 將處理後的資料匯出為 excel"""
        if not self._final_grouped_data:
            raise ValueError("No grouped data to export")

        df = pd.DataFrame()
        for group in self._final_grouped_data:
            for record in group.sale_records:
                record.location = group.location
            df = pd.concat([df, pd.DataFrame(group.sale_records)])
        df.to_excel(file_path, index=False)

    def errors_to_excel(self, file_path: str) -> None:
        """[Action] 將錯誤資料匯出為 excel"""
        df = pd.DataFrame([error for error in self._errors])
        df.to_excel(file_path, index=False)

    @staticmethod
    def _validator_schema_to_dataclass(data: SaleRecordValidatorSchema) -> SaleRecord:
        """[Data] Schema 轉換為 Dataclass"""
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
        """[Calc] 計算銷售記錄列表中相鄰日期的差異"""
        if not records:
            return []

        sorted_records = sorted(records, key=lambda x: x.date)

        for i in range(len(sorted_records)):
            if i == 0:
                sorted_records[i]._date_diff = 0
            else:
                diff_days = (
                    sorted_records[i].date - sorted_records[i - 1].date
                ).total_seconds() / (24 * 3600)
                sorted_records[i]._date_diff = diff_days

        return sorted_records

    @staticmethod
    def _assign_group_ids(
        records: list[SaleRecord], threshold_days: float = 45
    ) -> list[SaleRecord]:
        """[Calc] 為銷售記錄列表中的每個記錄分配組ID"""
        new_records = records.copy()
        group_id = 0
        new_records[0]._group_id = group_id
        for i in range(1, len(new_records)):
            if new_records[i]._date_diff > threshold_days:
                group_id += 1
            new_records[i]._group_id = group_id
        return new_records

    @staticmethod
    def _calculate_date_median(min_date: datetime, max_date: datetime) -> datetime:
        """[Calc] 計算日期中間值"""
        return min_date + (max_date - min_date) / 2

    @staticmethod
    def _compose_location_string(location: str, median_date: datetime) -> str:
        """[Calc] 組合場別和月份字串"""
        return (
            f"{location}{median_date.strftime('%y%m')}"
            if "'" not in location
            else location
        )
