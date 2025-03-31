"""
################################################################################
# Excel 響應模型模組
#
# 這個模組提供了適用於 Excel/Google Apps Script 的 API 響應模型
#
# 特點：
# - 扁平化數據結構
# - 分頁支持
# - 元數據支持（欄位定義和額外信息）
################################################################################
"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class PaginationModel(BaseModel):
    """分頁模型

    用於 API 分頁數據返回
    """

    page: int = Field(default=1, description="當前頁碼")
    page_size: int = Field(default=100, description="每頁記錄數量")
    total: int = Field(default=0, description="總記錄數量")
    total_pages: int = Field(default=1, description="總頁碼數量")


class ExcelResponseModel(BaseModel, Generic[T]):
    """Excel 數據響應模型

    用於 Excel/Google Apps Script 友好的數據格式
    """

    data: list[T] = Field(default_factory=list, description="數據列表")
    pagination: PaginationModel = Field(
        default_factory=PaginationModel, description="分頁信息"
    )
    meta: dict[str, Any] = Field(
        default_factory=dict, description="元數據，如欄位定義等"
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "data": [],
                "pagination": {
                    "page": 1,
                    "page_size": 100,
                    "total": 0,
                    "total_pages": 1,
                },
                "meta": {
                    "fields": ["id", "name", "value"],
                    "generated_at": "2025-03-31T00:00:00",
                },
            }
        },
    )
