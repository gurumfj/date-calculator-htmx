"""
Consolidated models module containing all data models, validators, and related classes.
"""

import logging
import re
from datetime import date, datetime
from enum import Enum
from typing import Any, Optional

import pandas as pd
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    field_validator,
    model_validator,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Base Classes and Enums
# ============================================================================

class BatchState(Enum):
    """批次狀態列舉

    用於追蹤雞隻批次的當前狀態，包含:
    - BREEDING: 養殖階段，雞隻正在生長
    - SALE: 銷售階段，開始進行銷售
    - COMPLETED: 結案階段，該批次已完成所有銷售
    """
    BREEDING = "breeding"
    SALE = "sale"
    COMPLETED = "completed"


class RecordEvent(Enum):
    """事件類型"""
    ADDED = "added"
    DELETED = "deleted"
    UPDATED = "updated"


class IBaseModel(BaseModel):
    """Base model for all validators"""
    unique_id: str | None = Field(default=None)


# ============================================================================
# Commands and Data Transfer Objects
# ============================================================================

class UploadFileCommand:
    """文件上傳命令"""
    def __init__(self, file):
        self.file = file


class ProcessingStats(BaseModel):
    """處理統計數據"""
    valid_count: int = 0
    invalid_count: int = 0
    duplicates_removed: int = 0
    inserted_count: int = 0
    deleted_count: int = 0
    duplicate_count: int = 0
    processing_time_ms: int = 0


class UploadResult(BaseModel):
    """上傳結果模型"""
    success: bool
    message: str
    file_type: str
    valid_count: int = 0
    invalid_count: int = 0
    duplicates_removed: int = 0
    inserted_count: int = 0
    deleted_count: int = 0
    duplicate_count: int = 0
    event_id: str
    processing_time_ms: int = 0
    data: list = []

    def to_dict(self) -> dict:
        """轉換為字典格式"""
        return {
            "success": self.success,
            "message": self.message,
            "file_type": self.file_type,
            "stats": {
                "valid_count": self.valid_count,
                "invalid_count": self.invalid_count,
                "duplicates_removed": self.duplicates_removed,
                "inserted_count": self.inserted_count,
                "deleted_count": self.deleted_count,
                "duplicate_count": self.duplicate_count,
                "processing_time_ms": self.processing_time_ms,
            },
            "event_id": self.event_id,
            "data_preview": self.data[:5] if self.data else []
        }

    def to_json(self, ensure_ascii: bool = True) -> str:
        """轉換為JSON格式"""
        import json
        return json.dumps(self.to_dict(), ensure_ascii=ensure_ascii, default=str)


# ============================================================================
# Validators for Data Processing
# ============================================================================

class BreedRecordValidator(IBaseModel):
    """農場原始數據模型，用於驗證和轉換 Excel 數據。

    此模型處理從 Excel 匯入的原始數據，提供數據驗證和轉換功能。
    所有字段都是可選的，因為原始數據可能不完整。
    """

    # 基本資料
    farm_name: str = Field(..., description="牧場名稱", alias="畜牧場名")
    address: str | None = Field(None, description="牧場地址", alias="畜牧場址")
    farm_license: str | None = Field(None, description="登記證號", alias="登記證號")

    # 畜主資料
    farmer_name: str | None = Field(None, description="畜主姓名", alias="畜主姓名")
    farmer_address: str | None = Field(
        None, description="畜主通訊地址", alias="畜主通訊地址"
    )

    # 批次資料
    batch_name: str = Field(..., description="場別", alias="場別")
    sub_location: str | None = Field(None, description="分場", alias="分場")
    veterinarian: str | None = Field(None, description="獸醫名稱", alias="Dr.")
    is_completed: bool = Field(False, description="是否完成", alias="結場")

    # 記錄資料
    chicken_breed: str = Field(..., description="雞的種類", alias="雞種")
    breed_date: date = Field(..., description="入雛日期", alias="入雛日期")
    chick_count: tuple[int, int] | None = Field(
        None, description="入雛數量", alias="入雛數量"
    )
    total_chick_count: int | None = Field(
        None, description="入雛總量", alias="入雛數量.1"
    )
    supplier: str | None = Field(None, description="種雞場名稱", alias="種雞場")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def pdna_to_none(cls, values: dict[str, Any]) -> dict[str, Any]:
        """將 pd.NA 轉換為 None"""
        try:
            for key, value in values.items():
                if pd.isna(value):
                    values[key] = None
                if isinstance(value, str):
                    values[key] = (
                        None if value.replace(" ", "") == "" else value.replace(" ", "")
                    )
            return values
        except Exception as e:
            raise ValueError(f"轉換 pd.NA 錯誤: {str(e)}")

    @field_validator("veterinarian", mode="before")
    @classmethod
    def invalid_input_value_to_unknown(cls, value: Any) -> str:
        try:
            if not isinstance(value, str):
                return "unknown"
            return value
        except Exception as e:
            raise ValueError(f"轉換場別錯誤: {str(e)}")

    @field_validator("chick_count", mode="before")
    @classmethod
    def validate_chick_count(cls, value: Any) -> tuple[int, int] | None:
        try:
            if isinstance(value, str):
                male, female = map(int, value.split("/"))
                return male, female
            return None
        except Exception as e:
            raise ValueError(f"轉換入雛數量錯誤: {str(e)}")

    @field_validator("total_chick_count", mode="before")
    @classmethod
    def validate_total_chick_count(cls, value: Any) -> int:
        try:
            if not isinstance(value, int):
                return int(value)
            return value or 0
        except Exception as e:
            raise ValueError(f"轉換入雛總量錯誤: {str(e)}")

    @field_validator("is_completed", mode="before")
    @classmethod
    def validate_is_completed(cls, value: Any) -> bool:
        try:
            if isinstance(value, str):
                return value.replace(" ", "").strip() == "結場"
            return False
        except Exception:
            return False

    @computed_field
    def breed_male(self) -> int:
        try:
            if self.chick_count:
                return self.chick_count[0]
            if self.chicken_breed == "閹雞":
                return self.total_chick_count or 0
            return self.total_chick_count // 2 if self.total_chick_count else 0
        except Exception as e:
            raise ValueError(f"計算公雞數量錯誤: {str(e)}")

    @computed_field
    def breed_female(self) -> int:
        try:
            if self.chick_count:
                return self.chick_count[1]
            if self.chicken_breed == "閹雞":
                return 0
            return self.total_chick_count // 2 if self.total_chick_count else 0
        except Exception as e:
            raise ValueError(f"計算母雞數量錯誤: {str(e)}")


class SaleRecordValidator(IBaseModel):
    """銷售記錄驗證模式

    負責驗證和轉換銷售記錄的原始數據，確保數據的完整性和一致性。
    主要功能包括：
    1. 數據類型轉換（字符串轉數字等）
    2. 空值處理（None, NaN等）
    3. 數據清理（去除多餘空格、特殊字符等）
    4. 數據驗證（必填字段、格式檢查等）

    配置說明：
    - populate_by_name=True：允許按字段名稱填充
    - from_attributes=True：支持從對象屬性讀取
    """

    is_completed: bool = Field(False, description="結案狀態", alias="結案")
    handler: str | None = Field(None, description="會磅狀態", alias="會磅")
    sale_date: date = Field(..., description="銷售日期", alias="日期")
    batch_name: str = Field(description="場別", alias="場別")
    customer: str = Field(description="客戶名稱", alias="客戶名稱")
    male_count: int = Field(0, ge=0, description="公豬數量", alias="公-隻數")
    female_count: int = Field(0, ge=0, description="母豬數量", alias="母-隻數")
    total_weight: float | None = Field(None, description="總重量", alias="總重\n(台斤)")
    total_price: float | None = Field(None, description="總價格", alias="總價")
    male_price: float | None = Field(None, alias="公-單價", description="公雞單價")
    female_price: float | None = Field(None, alias="母-單價", description="母雞單價")
    b_unpaid: bool = Field(True, description="未付款狀態", alias="未收")
    b_paid: bool = Field(False, description="已付款狀態", alias="實收")

    model_config = ConfigDict(
        str_strip_whitespace=True,
        populate_by_name=True,
        from_attributes=True,
    )

    @field_validator("sale_date", mode="before")
    @classmethod
    def clean_sale_date(cls, v: Any) -> date | None:
        try:
            if pd.isna(v):
                return None
            if isinstance(v, (datetime, pd.Timestamp)):
                return v.date()
            return v
        except (ValueError, TypeError):
            logger.warning(f"無法將 {v} 轉換為日期，使用預設值 None")
            return None

    @field_validator("batch_name", mode="before")
    @classmethod
    def clean_batch_name(cls, v: Any) -> str | None:
        try:
            if pd.isna(v):
                return None
            if isinstance(v, str):
                v = re.sub(r"--", "-", v)  # 將 "--" 替換為 "-"
                v = re.sub(r"\s+", "", v)  # 去除所有空格
                v = re.sub(r"-N", "", v)  # 移除 "-N"
                return v.strip()
            return None
        except (ValueError, TypeError):
            logger.warning(f"無法將 {v} 轉換為字串，使用預設值 None")
            return None

    @field_validator("male_count", "female_count", mode="before")
    @classmethod
    def clean_count(cls, v: Any) -> int:
        try:
            if pd.isna(v):
                return 0
            return int(float(v))
        except (ValueError, TypeError):
            logger.warning(f"無法將 {v} 轉換為整數，使用預設值 None")
            return 0

    @field_validator("is_completed", mode="before")
    @classmethod
    def clean_is_completed(cls, v: Any) -> bool:
        try:
            if isinstance(v, str):
                return v.replace(" ", "").strip() == "結案"
            return False
        except (ValueError, TypeError):
            logger.warning(f"無法將 {v} 轉換為布林值，使用預設值 False")
            return False

    @field_validator("b_unpaid", mode="before")
    @classmethod
    def clean_unpaid(cls, v: Any) -> bool:
        try:
            if pd.isna(v):
                return False
            if isinstance(v, str):
                return v == "未付"
            return bool(v)
        except (ValueError, TypeError):
            logger.warning(f"無法將 {v} 轉換為布林值，使用預設值 False")
            return True

    @field_validator("b_paid", mode="before")
    @classmethod
    def clean_paid(cls, v: Any) -> bool:
        try:
            if pd.isna(v):
                return False
            if isinstance(v, str):
                return True
            return bool(v)
        except (ValueError, TypeError):
            logger.warning(f"無法將 {v} 轉換為布林值，使用預設值 False")
            return False

    @computed_field
    def unpaid(self) -> bool:
        return self.b_unpaid and not self.b_paid

    @field_validator("handler", mode="before")
    @classmethod
    def clean_handler(cls, v: Any) -> str | None:
        try:
            if pd.isna(v):
                return None
            return v
        except (ValueError, TypeError):
            logger.warning(f"無法將 {v} 轉換為字串，使用預設值 None")
            return None

    # all float field
    @field_validator(
        "male_price", "female_price", "total_price", "total_weight", mode="before"
    )
    @classmethod
    def clean_float(cls, v: Any) -> float | None:
        try:
            if pd.isna(v):
                return None
            return float(v)
        except (ValueError, TypeError):
            logger.warning(f"無法將 {v} 轉換為浮點數，使用預設值 None")
            return None


class FeedRecordValidator(IBaseModel):
    # 必填資料
    batch_name: str = Field(..., description="場別", alias="場別")
    feed_date: datetime = Field(..., description="叫料日期", alias="日期")
    feed_manufacturer: str = Field(..., description="飼料廠", alias="飼料廠")
    feed_item: str = Field(..., description="品項", alias="品項")

    # 批次資料
    sub_location: str | None = Field(None, description="分場", alias="分場")
    is_completed: bool = Field(..., description="是否完成", alias="結場")

    # 記錄資料
    feed_week: str | None = Field(None, description="周齡", alias="周齡")
    feed_additive: str | None = Field(None, description="加藥", alias="加藥")
    feed_remark: str | None = Field(None, description="備註", alias="備註")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    # pd.nan to None
    @model_validator(mode="before")
    @classmethod
    def pdna_to_none(cls, values: dict[str, Any]) -> dict[str, Any]:
        try:
            # 必填欄位列表
            required_fields = ["場別", "日期", "飼料廠", "品項"]

            for key, value in values.items():
                # 處理 pd.NA 和 None
                if pd.isna(value):
                    # 如果是必填欄位但值為空，保留原值以便後續驗證報錯
                    if key in required_fields:
                        continue
                    values[key] = None
                    continue

                # 處理字串值
                if isinstance(value, str):
                    # 清除空白字符
                    cleaned_value = value.replace(" ", "")
                    # 如果清除空白後為空字串，且不是必填欄位，則設為 None
                    if cleaned_value == "":
                        if key in required_fields:
                            continue
                        values[key] = None
                    else:
                        values[key] = cleaned_value

                # 處理周齡欄位 - 確保數值型別能正確轉換為字串
                if key == "周齡" and value is not None:
                    values[key] = str(value)

            return values
        except Exception as e:
            raise ValueError(f"轉換 pd.NA 錯誤: {str(e)}")

    @field_validator("is_completed", mode="before")
    @classmethod
    def validate_is_completed(cls, value: Any) -> bool:
        try:
            if isinstance(value, str):
                return value.strip() == "結場"
            return False
        except Exception:
            return False  # 發生異常時返回 False


class FarmProductionValidator(BaseModel):
    """養殖場生產記錄驗證器 - 匹配資料庫表結構"""
    
    # 添加 unique_id 欄位以符合其他 validator 的格式
    unique_id: Optional[str] = Field(None, description="唯一識別碼")
    
    # 必填欄位
    batch_name: str = Field(..., description="批次名稱", alias="BatchName")
    
    # 基本資訊
    farm_location: Optional[str] = Field(None, description="場別", alias="場別")
    farmer: Optional[str] = Field(None, description="飼養者", alias="飼養者")
    chick_in_count: Optional[int] = Field(None, description="入雛數量", alias="入雛")
    chicken_out_count: Optional[int] = Field(None, description="出雞數量", alias="出雞")
    
    # 生產數據
    feed_weight: Optional[float] = Field(None, description="飼料總重量", alias="飼料總重")
    sale_weight_jin: Optional[float] = Field(None, description="銷售重量(斤)", alias="銷售重量_jin")
    fcr: Optional[float] = Field(None, description="換肉率 (Feed Conversion Ratio)", alias="換肉率")
    
    # 成本相關
    meat_cost: Optional[float] = Field(None, description="造肉成本", alias="造肉成本")
    avg_price: Optional[float] = Field(None, description="平均價格", alias="平均價")
    cost_price: Optional[float] = Field(None, description="成本價", alias="成本價")
    
    # 收支
    revenue: Optional[float] = Field(None, description="總收入", alias="總收入")
    expenses: Optional[float] = Field(None, description="總支出", alias="總支出")
    
    # 各項成本明細
    feed_cost: Optional[float] = Field(None, description="飼料費用", alias="飼料")
    vet_cost: Optional[float] = Field(None, description="獸醫防疫費用", alias="獸醫防疫")
    feed_med_cost: Optional[float] = Field(None, description="飼料自備藥費用", alias="飼料自備藥")
    farm_med_cost: Optional[float] = Field(None, description="公司藥品費用", alias="公司藥品")
    leg_band_cost: Optional[float] = Field(None, description="腳環費用", alias="腳環")
    chick_cost: Optional[float] = Field(None, description="雛雞款", alias="雛雞款")
    grow_fee: Optional[float] = Field(None, description="代養費", alias="代養費")
    catch_fee: Optional[float] = Field(None, description="抓工費用", alias="抓工")
    weigh_fee: Optional[float] = Field(None, description="磅單費用", alias="磅單")
    gas_cost: Optional[float] = Field(None, description="瓦斯費用", alias="瓦斯")
    
    @field_validator(
        'feed_weight', 'sale_weight_jin', 'fcr', 'meat_cost', 'avg_price', 'cost_price',
        'revenue', 'expenses', 'feed_cost', 'vet_cost', 'feed_med_cost', 'farm_med_cost',
        'leg_band_cost', 'chick_cost', 'grow_fee', 'catch_fee', 'weigh_fee', 'gas_cost',
        mode='before'
    )
    @classmethod
    def parse_float(cls, v):
        """解析浮點數值"""
        if v is None or v == '' or (hasattr(v, '__float__') and v != v):  # NaN check
            return None
        if isinstance(v, str):
            return float(v)
        return float(v)
    
    @field_validator(
        'farm_location', 'farmer',
        mode='before'
    )
    @classmethod
    def parse_string(cls, v):
        """解析字串值，處理 NaN"""
        if v is None or v == '' or (hasattr(v, '__float__') and v != v):  # NaN check
            return None
        return str(v)
    
    class Config:
        # 允許使用field名稱作為JSON key
        populate_by_name = True


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    # Enums and base classes
    "BatchState",
    "RecordEvent", 
    "IBaseModel",
    
    # Commands and DTOs
    "UploadFileCommand",
    "ProcessingStats",
    "UploadResult",
    
    # Validators
    "BreedRecordValidator",
    "SaleRecordValidator", 
    "FeedRecordValidator",
    "FarmProductionValidator",
]