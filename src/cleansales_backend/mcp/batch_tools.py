"""
################################################################################
# 批次工具模組
#
# 這個模組提供了與批次相關的工具函數，用於在 MCP 中訪問批次數據。
#
# 主要功能：
# 1. 獲取批次數據
# 2. 過濾批次數據
# 3. 提供構建 MCP 工具的裝飾器
################################################################################
"""

import logging
from datetime import datetime
from typing import List, Literal

import requests

from cleansales_backend.processors.interface.processors_interface import IResponse

logger = logging.getLogger(__name__)


def get_batches(
    batch_name: str | None = None,
    breed_type: Literal["黑羽", "古早", "舍黑", "閹雞"] | None = None,
    batch_status: list[Literal["completed", "breeding", "sale"]] | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    api_url: str = "http://localhost:8888",
) -> IResponse:
    """獲取批次數據

    Args:
        batch_name: 批次名稱，如果為 None 則不過濾
        breed_type: 雞種類型，如果為 None 則不過濾
        batch_status: 批次狀態列表，如果為 None 則不過濾
        start_date: 開始日期，如果為 None 則不過濾
        end_date: 結束日期，如果為 None 則不過濾
        api_url: API 基礎 URL，默認為 http://localhost:8888

    Returns:
        IResponse: 包含批次數據的標準響應對象
    """
    try:
        # 構建請求參數
        params = {}
        if batch_name:
            params["batch_name"] = batch_name
        if breed_type:
            params["breed_type"] = breed_type
        if batch_status:
            params["batch_status"] = batch_status
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()

        # 發送請求
        url = f"{api_url}/api/batch"
        response = requests.get(url, params=params)

        # 檢查響應
        if response.status_code == 200:
            data = response.json()
            return IResponse(
                success=True,
                message=f"成功獲取 {len(data)} 筆批次數據",
                content={"data": data},
            )
        elif response.status_code == 304:
            return IResponse(
                success=True,
                message="數據未變更",
                content={"data": []},
            )
        else:
            return IResponse(
                success=False,
                message=f"API 請求失敗，狀態碼: {response.status_code}",
                content={"error": response.text},
            )
    except Exception as e:
        logger.error(f"獲取批次數據時發生錯誤: {e}")
        return IResponse(
            success=False,
            message=f"獲取批次數據時發生錯誤: {str(e)}",
            content={"error": str(e), "type": type(e).__name__},
        )


def get_batch_by_name(
    batch_name: str,
    api_url: str = "http://localhost:8888",
) -> IResponse:
    """根據批次名稱獲取批次數據

    Args:
        batch_name: 批次名稱
        api_url: API 基礎 URL，默認為 http://localhost:8888

    Returns:
        IResponse: 包含批次數據的標準響應對象
    """
    return get_batches(batch_name=batch_name, api_url=api_url)


def get_batches_by_breed(
    breed_type: Literal["黑羽", "古早", "舍黑", "閹雞"],
    api_url: str = "http://localhost:8888",
) -> IResponse:
    """根據雞種類型獲取批次數據

    Args:
        breed_type: 雞種類型
        api_url: API 基礎 URL，默認為 http://localhost:8888

    Returns:
        IResponse: 包含批次數據的標準響應對象
    """
    return get_batches(breed_type=breed_type, api_url=api_url)


def get_batches_by_status(
    batch_status: List[Literal["completed", "breeding", "sale"]],
    api_url: str = "http://localhost:8888",
) -> IResponse:
    """根據批次狀態獲取批次數據

    Args:
        batch_status: 批次狀態列表
        api_url: API 基礎 URL，默認為 http://localhost:8888

    Returns:
        IResponse: 包含批次數據的標準響應對象
    """
    return get_batches(batch_status=batch_status, api_url=api_url)


def get_batches_by_date_range(
    start_date: datetime,
    end_date: datetime,
    api_url: str = "http://localhost:8888",
) -> IResponse:
    """根據日期範圍獲取批次數據

    Args:
        start_date: 開始日期
        end_date: 結束日期
        api_url: API 基礎 URL，默認為 http://localhost:8888

    Returns:
        IResponse: 包含批次數據的標準響應對象
    """
    return get_batches(start_date=start_date, end_date=end_date, api_url=api_url)
