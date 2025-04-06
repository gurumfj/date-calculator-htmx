"""
################################################################################
# 事件定義模組
#
# 這個模組提供了系統中使用的所有事件類型定義，包括：
# 1. 處理事件枚舉
# 2. 系統事件枚舉
# 3. 其他事件類型
#
# 主要功能：
# - 定義處理事件枚舉
# - 定義系統事件枚舉
################################################################################
"""

from enum import Enum


class ProcessEvent(str, Enum):
    """處理事件枚舉"""

    SALES_PROCESSING_STARTED = "販售資料上傳開始"
    SALES_PROCESSING_COMPLETED = "販售資料上傳完成"
    SALES_PROCESSING_FAILED = "販售資料上傳失敗"
    BREEDS_PROCESSING_STARTED = "入雛資料上傳開始"
    BREEDS_PROCESSING_COMPLETED = "入雛資料上傳完成"
    BREEDS_PROCESSING_FAILED = "入雛資料上傳失敗"
    FEEDS_PROCESSING_STARTED = "飼料記錄上傳開始"
    FEEDS_PROCESSING_COMPLETED = "飼料記錄上傳完成"
    FEEDS_PROCESSING_FAILED = "飼料記錄上傳失敗"


class SystemEvent(str, Enum):
    """系統事件枚舉"""

    CACHE_CLEAR = "清除緩存"
