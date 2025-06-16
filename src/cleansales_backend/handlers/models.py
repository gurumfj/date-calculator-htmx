from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Dict, List


@dataclass
class UploadResult:
    """上傳處理結果"""
    success: bool
    message: str
    file_type: str
    valid_count: int
    invalid_count: int
    event_id: str  # 必需的 event_id 欄位
    data: List[Dict[str, Any]] = field(default_factory=list)
    
    # 處理統計欄位
    duplicates_removed: int = 0
    inserted_count: int = 0
    deleted_count: int = 0
    duplicate_count: int = 0
    processing_time_ms: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式以保持向後兼容性"""
        result = {
            "success": self.success,
            "message": self.message,
            "file_type": self.file_type,
            "valid_count": self.valid_count,
            "invalid_count": self.invalid_count,
            "event_id": self.event_id,  # 總是包含 event_id
            "data": self.data,
        }
        
        # 只在有值時添加可選欄位
        if self.duplicates_removed > 0:
            result["duplicates_removed"] = self.duplicates_removed
        if self.inserted_count > 0:
            result["inserted_count"] = self.inserted_count
        if self.deleted_count > 0:
            result["deleted_count"] = self.deleted_count
        if self.duplicate_count > 0:
            result["duplicate_count"] = self.duplicate_count
        if self.processing_time_ms > 0:
            result["processing_time_ms"] = self.processing_time_ms
            
        return result
    
    def to_json(self, ensure_ascii: bool = False, indent: int | None = None) -> str:
        """轉換為 JSON 字符串"""
        def serialize_datetime(obj):
            """JSON序列化日期時間物件"""
            if isinstance(obj, (datetime, date)):
                return obj.isoformat()
            raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")
        
        return json.dumps(
            self.to_dict(), 
            default=serialize_datetime, 
            ensure_ascii=ensure_ascii,
            indent=indent
        )


@dataclass
class ProcessingStats:
    """處理統計信息"""
    inserted_count: int
    deleted_count: int
    duplicate_count: int
    duplicates_removed: int