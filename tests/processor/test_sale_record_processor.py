from datetime import datetime
from dataclasses import asdict

import pandas as pd
import pytest

from cleansales_refactor.models import (
    ErrorMessage,
    ProcessingResult,
    SaleRecord,
    SaleRecordsGroupByLocation,
)
from cleansales_refactor.processor.sale_record_processor import SaleRecordProcessor


@pytest.fixture
def sample_sale_records() -> list[SaleRecord]:
    """建立測試用的銷售記錄"""
    return [
        SaleRecord(
            closed=True,
            handler="測試員A",
            date=datetime(2024, 1, 1),
            location="台北",
            customer="客戶A",
            male_count=2,
            female_count=1,
            total_weight=150.5,
            total_price=3000,
            male_price=2000,
            female_price=1000,
            unpaid=0,
        ),
        SaleRecord(
            closed=True,
            handler="測試員A",
            date=datetime(2024, 1, 15),
            location="台北",
            customer="客戶B",
            male_count=1,
            female_count=2,
            total_weight=120.0,
            total_price=2500,
            male_price=1000,
            female_price=1500,
            unpaid=0,
        ),
    ]


@pytest.fixture
def sample_dataframe(sample_sale_records) -> pd.DataFrame:
    """建立測試用的 DataFrame"""
    records_dict = [asdict(record) for record in sample_sale_records]
    return pd.DataFrame(records_dict)


def test_process_data_success(sample_dataframe):
    """測試正常資料處理流程"""
    result = SaleRecordProcessor.process_data(sample_dataframe)

    assert isinstance(result, ProcessingResult)
    assert len(result.grouped_data) > 0
    assert len(result.errors) == 0

    # 檢查分組結果
    first_group = result.grouped_data[0]
    assert isinstance(first_group, SaleRecordsGroupByLocation)
    assert "台北" in first_group.location
    assert len(first_group.sale_records) == 2


def test_validate_and_clean_records_with_invalid_data():
    """測試資料驗證和清理 - 無效資料"""
    invalid_data = pd.DataFrame(
        [
            {
                "closed": True,
                "handler": "測試員A",
                "date": "invalid_date",  # 無效日期
                "location": "台北",
                "customer": "客戶A",
                "male_count": -1,  # 無效數量
                "female_count": 1,
                "total_weight": 150.5,
                "total_price": 3000,
                "male_price": 2000,
                "female_price": 1000,
                "unpaid": 0,
            }
        ]
    )

    cleaned_records, errors = SaleRecordProcessor._validate_and_clean_records(
        invalid_data
    )

    assert len(cleaned_records) == 0
    assert len(errors) == 1
    assert isinstance(errors[0], ErrorMessage)


def test_group_by_location(sample_sale_records):
    """測試按位置分組"""
    groups = SaleRecordProcessor._group_by_location(sample_sale_records)

    assert len(groups) == 1
    assert "台北" in groups
    assert len(groups["台北"]) == 2


def test_process_groups(sample_sale_records):
    """測試處理分組"""
    groups = {"台北": sample_sale_records}
    processed_records = SaleRecordProcessor._process_groups(groups)

    assert len(processed_records) == 2
    assert all(hasattr(record, "_date_diff") for record in processed_records)
    assert all(hasattr(record, "_group_id") for record in processed_records)


def test_create_final_groups(sample_sale_records):
    """測試創建最終分組"""
    # 先處理記錄，添加必要的屬性
    groups = {"台北": sample_sale_records}
    processed_records = SaleRecordProcessor._process_groups(groups)

    final_groups = SaleRecordProcessor._create_final_groups(processed_records)

    assert len(final_groups) > 0
    assert all(isinstance(group, SaleRecordsGroupByLocation) for group in final_groups)
    assert all(len(group.sale_records) > 0 for group in final_groups)
