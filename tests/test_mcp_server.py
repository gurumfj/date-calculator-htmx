"""測試 MCP Server 功能

此模組包含對 MCP Server 中各個功能的單元測試
主要測試以下功能：
- 最近活躍位置查詢
"""
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from cleansales_backend.domain.models.batch_aggregate import BatchAggregate
from cleansales_backend.domain.models.breed_record import BreedRecord
from cleansales_backend.domain.models.sale_record import SaleRecord
from cleansales_backend.mcp.server import get_recently_active_location


def create_mock_batch_aggregate(
    sales_dates: list[date],
    batch_number: int = 1
) -> BatchAggregate:
    """創建模擬的 BatchAggregate 對象
    
    Args:
        sales_dates: 銷售日期列表
        batch_number: 批次編號，用於區分不同批次
    """
    batch_name = f"測試批次{batch_number}"
    
    mock_sales = [
        SaleRecord(
            closed=None,
            handler="測試人員",
            sale_date=datetime.combine(sale_date, datetime.min.time()),
            location=batch_name,  # 使用批次名稱作為 location
            customer="測試客戶",
            male_count=10,
            female_count=10,
            total_weight=100.0,
            total_price=10000.0,
            male_price=100.0,
            female_price=90.0,
            unpaid=None
        )
        for sale_date in sales_dates
    ]
    
    breed_date = datetime.combine(
        min(sales_dates) - timedelta(days=30),
        datetime.min.time()
    )
    mock_breeds = [
        BreedRecord(
            farm_name="測試農場",
            address="測試地址",
            farm_license="測試牌照",
            farmer_name="測試農夫",
            farmer_address="測試農夫地址",
            batch_name=batch_name,  # 使用一致的批次名稱
            veterinarian="測試獸醫",
            chicken_breed="測試品種",
            supplier="測試供應商",
            breed_date=breed_date,
            male=100,
            female=100,
            sub_location="測試子地點",
            is_completed=None
        )
    ]
    
    return BatchAggregate(breeds=mock_breeds, sales=mock_sales)


@pytest.mark.parametrize(
    "test_data,days,expected_count",
    [
        # 測試場景1：所有批次都在活躍期內
        (
            [
                [date(2025, 3, 15), date(2025, 3, 16)],  # 批次1：最近的銷售
                [date(2025, 3, 10), date(2025, 3, 12)],  # 批次2：較近的銷售
            ],
            14,
            2
        ),
        # 測試場景2：部分批次在活躍期內
        (
            [
                [date(2025, 3, 15), date(2025, 3, 16)],  # 批次1：在活躍期內
                [date(2025, 2, 1), date(2025, 2, 5)],    # 批次2：超出活躍期
            ],
            14,
            1
        ),
        # 測試場景3：所有批次都超出活躍期
        (
            [
                # 批次1：超出活躍期
                [date(2025, 2, 1), date(2025, 2, 5)],
                # 批次2：超出活躍期
                [date(2025, 1, 1), date(2025, 1, 5)],
            ],
            14,
            0
        ),
    ]
)
def test_get_recently_active_location(
    test_data: list[list[date]],
    days: int,
    expected_count: int
) -> None:
    """測試獲取最近活躍位置功能
    
    測試不同場景下的批次篩選邏輯：
    1. 所有批次都在活躍期內
    2. 部分批次在活躍期內
    3. 所有批次都超出活躍期
    """
    # 準備測試數據
    mock_aggregates = [
        create_mock_batch_aggregate(sales_dates, batch_number=i + 1)
        for i, sales_dates in enumerate(test_data)
    ]
    
    # 模擬數據庫會話和查詢服務
    mock_session = MagicMock()
    mock_session_context = MagicMock()
    mock_session_context.__enter__.return_value = mock_session
    mock_session_context.__exit__.return_value = None

    with patch(
        'cleansales_backend.mcp.server.db.get_session',
        return_value=mock_session_context
    ), patch(
        'cleansales_backend.mcp.server.query_service.get_batch_aggregates'
    ) as mock_get_aggregates:
        mock_get_aggregates.return_value = mock_aggregates
        
        # 固定當前時間為 2025-03-16
        with patch(
            'cleansales_backend.mcp.server.get_current_time',
            return_value=datetime(2025, 3, 16)
        ):
            # 執行測試
            result = get_recently_active_location(days=days)
            
            # 驗證結果
            # 驗證結果數量
            result_count = len(result.split('\n')) if result else 0
            assert result_count == expected_count
            
            # 驗證模擬函數被正確調用
            mock_get_aggregates.assert_called_once_with(mock_session)
