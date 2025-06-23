"""
File upload handling and data processing functionality.
"""

import hashlib
import json
import logging
import time
import uuid
from datetime import datetime
from io import BytesIO
from typing import Any, Dict, List, Tuple

import pandas as pd

from core_models import (
    BreedRecordValidator,
    FarmProductionValidator,
    FeedRecordValidator,
    SaleRecordValidator,
    UploadFileCommand,
    UploadResult,
)
from db_init import get_db_connection_context

logger = logging.getLogger(__name__)


class FileTypeDetector:
    @staticmethod
    def detect_file_type(df: pd.DataFrame) -> str:
        columns = set(df.columns.str.strip())

        breed_indicators = {"畜牧場名", "入雛日期", "雞種", "種雞場"}
        if breed_indicators.intersection(columns):
            return "breed"

        sale_indicators = {"客戶名稱", "公-隻數", "母-隻數", "總價"}
        if sale_indicators.intersection(columns):
            return "sale"

        feed_indicators = {"飼料廠", "品項", "周齡"}
        if feed_indicators.intersection(columns):
            return "feed"

        # 養殖場生產記錄檢測
        farm_production_indicators = {"BatchName", "換肉率", "飼料總重", "銷售重量_jin", "總收入", "總支出"}
        if len(farm_production_indicators.intersection(columns)) >= 3:
            return "farm_production"

        return "unknown"


class EventLogger:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def log_upload_event(
        self,
        event_id: str,
        file_name: str,
        file_size: int,
        file_type: str,
        processing_status: str,
        processing_time_ms: int,
        valid_count: int = 0,
        invalid_count: int = 0,
        duplicates_removed: int = 0,
        inserted_count: int = 0,
        deleted_count: int = 0,
        duplicate_count: int = 0,
        error_message: str | None = None,
        metadata: dict | None = None,
    ) -> str:
        with get_db_connection_context() as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO upload_events (
                        event_id, file_type, file_name, file_size, processing_status,
                        valid_count, invalid_count, duplicates_removed, inserted_count,
                        deleted_count, duplicate_count, error_message, processing_time_ms,
                        metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        event_id,
                        file_type,
                        file_name,
                        file_size,
                        processing_status,
                        valid_count,
                        invalid_count,
                        duplicates_removed,
                        inserted_count,
                        deleted_count,
                        duplicate_count,
                        error_message,
                        processing_time_ms,
                        json.dumps(metadata) if metadata else None,
                    ),
                )
                return event_id
            except Exception as e:
                logger.error(f"記錄上傳事件失敗: {e}")
                return ""


class DataProcessor:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.validators = {
            "breed": (
                BreedRecordValidator,
                "breed",
                [
                    "unique_id",
                    "farm_name",
                    "address",
                    "farm_license",
                    "farmer_name",
                    "farmer_address",
                    "batch_name",
                    "sub_location",
                    "veterinarian",
                    "is_completed",
                    "chicken_breed",
                    "breed_date",
                    "supplier",
                    "breed_male",
                    "breed_female",
                    "event_id",
                    "created_at",
                ],
            ),
            "sale": (
                SaleRecordValidator,
                "sale",
                [
                    "unique_id",
                    "is_completed",
                    "handler",
                    "sale_date",
                    "batch_name",
                    "customer",
                    "male_count",
                    "female_count",
                    "total_weight",
                    "total_price",
                    "male_price",
                    "female_price",
                    "unpaid",
                    "event_id",
                    "created_at",
                ],
            ),
            "feed": (
                FeedRecordValidator,
                "feed",
                [
                    "unique_id",
                    "batch_name",
                    "feed_date",
                    "feed_manufacturer",
                    "feed_item",
                    "sub_location",
                    "is_completed",
                    "feed_week",
                    "feed_additive",
                    "feed_remark",
                    "event_id",
                    "created_at",
                ],
            ),
            "farm_production": (
                FarmProductionValidator,
                "farm_production",
                [
                    "unique_id",
                    "batch_name",
                    "farm_location",
                    "farmer",
                    "chick_in_count",
                    "chicken_out_count",
                    "feed_weight",
                    "sale_weight_jin",
                    "fcr",
                    "meat_cost",
                    "avg_price",
                    "cost_price",
                    "revenue",
                    "expenses",
                    "feed_cost",
                    "vet_cost",
                    "feed_med_cost",
                    "farm_med_cost",
                    "leg_band_cost",
                    "chick_cost",
                    "grow_fee",
                    "catch_fee",
                    "weigh_fee",
                    "gas_cost",
                    "event_id",
                    "created_at",
                ],
            ),
        }


    def validate_and_process_data(
        self, df: pd.DataFrame, file_type: str, event_id: str
    ) -> Tuple[List[Dict[str, Any]], int]:
        if file_type not in self.validators:
            raise ValueError(f"Unsupported file type: {file_type}")

        validator_class, _, _ = self.validators[file_type]
        valid_records = []
        invalid_count = 0

        for _, row in df.iterrows():
            try:
                # 轉換 pandas Series 為字典進行驗證
                row_dict = row.to_dict()
                validated_record = validator_class.model_validate(row_dict)

                # 生成 unique_id
                validated_record.unique_id = hashlib.sha256(
                    validated_record.model_dump_json(exclude="unique_id").encode()
                ).hexdigest()[:10]

                record_dict = validated_record.model_dump()
                record_dict["created_at"] = datetime.now().isoformat()
                record_dict["event_id"] = event_id
                valid_records.append(record_dict)
            except Exception as e:
                logger.warning(f"Record validation failed for {file_type}: {e}")
                invalid_count += 1

        return valid_records, invalid_count

    def sync_database(self, file_type: str, records: List[Dict[str, Any]]) -> Tuple[int, int, int, int]:
        if file_type not in self.validators:
            raise ValueError(f"Unsupported file type: {file_type}")

        _, table_name, columns = self.validators[file_type]

        unique_records = {}
        for record in records:
            unique_id = record.get("unique_id")
            if unique_id:
                unique_records[unique_id] = record

        deduplicated_records = list(unique_records.values())
        duplicates_removed = len(records) - len(deduplicated_records)

        with get_db_connection_context() as conn:
            cursor = conn.execute(f"SELECT unique_id FROM {table_name}")
            existing_ids = {row[0] for row in cursor.fetchall()}
            upload_ids = {record["unique_id"] for record in deduplicated_records}

            ids_to_delete = existing_ids - upload_ids
            ids_to_insert = upload_ids - existing_ids
            duplicate_count = len(upload_ids & existing_ids)

            deleted_count = 0
            if ids_to_delete:
                placeholders = ",".join(["?" for _ in ids_to_delete])
                conn.execute(f"DELETE FROM {table_name} WHERE unique_id IN ({placeholders})", list(ids_to_delete))
                deleted_count = len(ids_to_delete)

            records_to_insert = [r for r in deduplicated_records if r["unique_id"] in ids_to_insert]

            inserted_count = 0
            if records_to_insert:
                placeholders = ", ".join(["?" for _ in columns])
                insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"

                for record in records_to_insert:
                    values = []
                    for col in columns:
                        value = record.get(col)
                        if col.endswith("_date") and hasattr(value, "isoformat"):
                            value = value.isoformat()
                        elif isinstance(value, bool):
                            value = int(value)
                        values.append(value)
                    conn.execute(insert_sql, values)
                inserted_count = len(records_to_insert)

            return inserted_count, deleted_count, duplicate_count, duplicates_removed
    
    def get_data_by_event_id(self, file_type: str, event_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """根據 event_id 從資料庫查詢實際儲存的資料"""
        if file_type not in self.validators:
            return []
        
        _, table_name, _ = self.validators[file_type]
        
        with get_db_connection_context() as conn:
            try:
                cursor = conn.execute(
                    f"SELECT * FROM {table_name} WHERE event_id = ? LIMIT ?",
                    (event_id, limit)
                )
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            except Exception as e:
                logger.error(f"查詢 event_id {event_id} 資料失敗: {e}")
                return []


class UploadCommandHandler:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.file_detector = FileTypeDetector()
        self.event_logger = EventLogger(db_path)
        self.data_processor = DataProcessor(db_path)

    async def handle(self, command: UploadFileCommand) -> UploadResult:
        start_time = time.time()
        event_id = str(uuid.uuid4())

        try:
            filebuffer = await command.file.read()
            file_size = len(filebuffer)
            bytes_io = BytesIO(filebuffer)
            df = pd.read_excel(bytes_io)

            file_type = self.file_detector.detect_file_type(df)

            if file_type == "unknown":
                processing_time_ms = int((time.time() - start_time) * 1000)
                self.event_logger.log_upload_event(
                    event_id=event_id,
                    file_name=command.file.filename or "unknown",
                    file_size=file_size,
                    file_type=file_type,
                    processing_status="failed",
                    processing_time_ms=processing_time_ms,
                    error_message="無法識別檔案類型",
                    metadata={"columns": list(df.columns)},
                )
                return UploadResult(
                    success=False,
                    message="無法識別檔案類型，請確認欄位名稱是否正確",
                    file_type=file_type,
                    valid_count=0,
                    invalid_count=0,
                    event_id=event_id,
                    data=[],
                )

            valid_records, invalid_count = self.data_processor.validate_and_process_data(df, file_type, event_id)

            if not valid_records:
                processing_time_ms = int((time.time() - start_time) * 1000)
                self.event_logger.log_upload_event(
                    event_id=event_id,
                    file_name=command.file.filename or "unknown",
                    file_size=file_size,
                    file_type=file_type,
                    processing_status="failed",
                    processing_time_ms=processing_time_ms,
                    invalid_count=invalid_count,
                    error_message="沒有有效的數據記錄",
                )
                return UploadResult(
                    success=False,
                    message="沒有有效的數據記錄",
                    file_type=file_type,
                    valid_count=0,
                    invalid_count=invalid_count,
                    event_id=event_id,
                    data=[],
                )

            inserted_count, deleted_count, duplicate_count, duplicates_removed = self.data_processor.sync_database(
                file_type, valid_records
            )

            message_parts = []
            if inserted_count > 0:
                message_parts.append(f"新增 {inserted_count} 條記錄")
            if deleted_count > 0:
                message_parts.append(f"刪除 {deleted_count} 條記錄")
            if duplicate_count > 0:
                message_parts.append(f"保持 {duplicate_count} 條已存在記錄")
            if invalid_count > 0:
                message_parts.append(f"跳過 {invalid_count} 條無效記錄")
            if duplicates_removed > 0:
                message_parts.append(f"去重 {duplicates_removed} 條重複記錄")

            final_message = (
                f"處理 {file_type} 資料：" + "，".join(message_parts) if message_parts else f"處理 {file_type} 資料完成"
            )

            processing_time_ms = int((time.time() - start_time) * 1000)
            self.event_logger.log_upload_event(
                event_id=event_id,
                file_name=command.file.filename or "unknown",
                file_size=file_size,
                file_type=file_type,
                processing_status="completed",
                processing_time_ms=processing_time_ms,
                valid_count=len(valid_records) - duplicates_removed,
                invalid_count=invalid_count,
                duplicates_removed=duplicates_removed,
                inserted_count=inserted_count,
                deleted_count=deleted_count,
                duplicate_count=duplicate_count,
                metadata={
                    "total_rows": len(df),
                    "columns": list(df.columns),
                    "table_name": self.data_processor.validators[file_type][1],
                },
            )

            # 從資料庫查詢實際儲存的資料
            database_data = self.data_processor.get_data_by_event_id(file_type, event_id, limit=50)
            
            return UploadResult(
                success=True,
                message=final_message,
                file_type=file_type,
                valid_count=len(valid_records) - duplicates_removed,
                invalid_count=invalid_count,
                duplicates_removed=duplicates_removed,
                inserted_count=inserted_count,
                deleted_count=deleted_count,
                duplicate_count=duplicate_count,
                event_id=event_id,
                processing_time_ms=processing_time_ms,
                data=database_data,
            )

        except Exception as e:
            logger.error(f"上傳處理失敗: {e}")
            processing_time_ms = int((time.time() - start_time) * 1000)
            self.event_logger.log_upload_event(
                event_id=event_id,
                file_name=command.file.filename or "unknown",
                file_size=len(filebuffer) if "filebuffer" in locals() else 0,
                file_type=file_type if "file_type" in locals() else "unknown",
                processing_status="error",
                processing_time_ms=processing_time_ms,
                valid_count=len(valid_records) if "valid_records" in locals() else 0,
                invalid_count=invalid_count if "invalid_count" in locals() else 0,
                error_message=f"上傳處理失敗: {str(e)}",
            )
            return UploadResult(
                success=False,
                message=f"上傳處理失敗: {str(e)}",
                file_type=file_type if "file_type" in locals() else "unknown",
                valid_count=0,
                invalid_count=invalid_count if "invalid_count" in locals() else 0,
                event_id=event_id,
                data=[],
            )