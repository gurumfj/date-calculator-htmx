from __future__ import annotations

import os
import tempfile
from io import BytesIO
from typing import Generator
from unittest.mock import AsyncMock, Mock

import pandas as pd
import pytest

from cleansales_backend.commands.upload_commands import UploadFileCommand
from cleansales_backend.handlers.upload_handler import (
    DataProcessor,
    EventLogger,
    FileTypeDetector,
    UploadCommandHandler,
)


class TestFileTypeDetector:
    def test_detect_breed_file(self) -> None:
        df = pd.DataFrame({
            "畜牧場名": ["測試農場"],
            "入雛日期": ["2024-01-01"],  
            "雞種": ["白肉雞"],
            "種雞場": ["測試種雞場"]
        })
        
        file_type = FileTypeDetector.detect_file_type(df)
        assert file_type == "breed"
    
    def test_detect_sale_file(self) -> None:
        df = pd.DataFrame({
            "客戶名稱": ["測試客戶"],
            "公-隻數": [100],
            "母-隻數": [200],
            "總價": [10000]
        })
        
        file_type = FileTypeDetector.detect_file_type(df)
        assert file_type == "sale"
    
    def test_detect_feed_file(self) -> None:
        df = pd.DataFrame({
            "飼料廠": ["測試飼料廠"], 
            "品項": ["測試飼料"],
            "周齡": [1]
        })
        
        file_type = FileTypeDetector.detect_file_type(df)
        assert file_type == "feed"
    
    def test_detect_unknown_file(self) -> None:
        df = pd.DataFrame({
            "無關欄位1": ["測試"],
            "無關欄位2": ["測試"]
        })
        
        file_type = FileTypeDetector.detect_file_type(df)
        assert file_type == "unknown"


class TestEventLogger:
    @pytest.fixture
    def temp_db_path(self) -> Generator[str, None, None]:
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        # 初始化測試數據庫
        from cleansales_backend.database.init import init_db
        init_db(db_path)
        
        yield db_path
        os.unlink(db_path)
    
    def test_log_upload_event_success(self, temp_db_path: str) -> None:
        logger = EventLogger(temp_db_path)
        
        event_id = logger.log_upload_event(
            event_id="test-event-123",
            file_name="test.xlsx",
            file_size=1000,
            file_type="breed",
            processing_status="completed",
            processing_time_ms=500,
            valid_count=10,
            invalid_count=2,
            inserted_count=8
        )
        
        assert event_id == "test-event-123"
        
        # 驗證事件是否正確記錄
        conn = logger.get_db_connection()
        cursor = conn.execute("SELECT * FROM upload_events WHERE event_id = ?", (event_id,))
        result = cursor.fetchone()
        conn.close()
        
        assert result is not None
        assert result['file_name'] == "test.xlsx"
        assert result['file_type'] == "breed"
        assert result['processing_status'] == "completed"


class TestDataProcessor:
    @pytest.fixture 
    def temp_db_path(self):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        from cleansales_backend.database.init import init_db
        init_db(db_path)
        
        yield db_path
        os.unlink(db_path)
    
    def test_validate_and_process_breed_data(self, temp_db_path: str) -> None:
        processor = DataProcessor(temp_db_path)
        
        df = pd.DataFrame({
            "畜牧場名": ["測試農場"],
            "入雛日期": ["2024-01-01"],
            "雞種": ["白肉雞"],
            "場別": ["TEST001"],
            "種雞場": ["測試種雞場"],
            "入雛數量": ["100/200"]
        })
        
        valid_records, invalid_count = processor.validate_and_process_data(
            df, "breed", "test-event"
        )
        
        assert len(valid_records) == 1
        assert invalid_count == 0
        assert valid_records[0]['farm_name'] == "測試農場"
        assert valid_records[0]['batch_name'] == "TEST001"
        assert valid_records[0]['event_id'] == "test-event"
    
    def test_sync_database_insert_new_records(self, temp_db_path: str) -> None:
        processor = DataProcessor(temp_db_path)
        
        records = [{
            'unique_id': 'test123',
            'farm_name': '測試農場',
            'batch_name': 'TEST001',
            'chicken_breed': '白肉雞',
            'breed_date': '2024-01-01',
            'breed_male': 100,
            'breed_female': 200,
            'event_id': 'test-event',
            'created_at': '2024-01-01T00:00:00',
            'address': None,
            'farm_license': None,
            'farmer_name': None,
            'farmer_address': None,
            'sub_location': None,
            'veterinarian': None,
            'is_completed': 0,
            'supplier': None
        }]
        
        inserted, deleted, duplicate, duplicates_removed = processor.sync_database("breed", records)
        
        assert inserted == 1
        assert deleted == 0
        assert duplicate == 0
        assert duplicates_removed == 0


class TestUploadCommandHandler:
    @pytest.fixture
    def temp_db_path(self) -> Generator[str, None, None]:
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        from cleansales_backend.database.init import init_db
        init_db(db_path)
        
        yield db_path
        os.unlink(db_path)
    
    @pytest.fixture
    def mock_excel_file(self) -> Mock:
        # 創建模擬的Excel文件
        df = pd.DataFrame({
            "畜牧場名": ["測試農場"],
            "入雛日期": ["2024-01-01"],
            "雞種": ["白肉雞"],
            "場別": ["TEST001"],
            "種雞場": ["測試種雞場"],
            "入雛數量": ["100/200"]
        })
        
        excel_buffer = BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        
        mock_file = Mock()
        mock_file.filename = "test.xlsx"
        mock_file.read = AsyncMock(return_value=excel_buffer.getvalue())
        
        return mock_file
    
    @pytest.mark.asyncio
    async def test_handle_successful_upload(self, temp_db_path: str, mock_excel_file: Mock) -> None:
        handler = UploadCommandHandler(temp_db_path)
        command = UploadFileCommand(file=mock_excel_file)
        
        result = await handler.handle(command)
        
        assert result.success is True
        assert result.file_type == "breed"
        assert result.valid_count == 1
        assert result.invalid_count == 0
        assert result.inserted_count == 1
        assert result.event_id is not None
        
        # 驗證返回的資料來自資料庫且包含 event_id
        assert len(result.data) == 1
        assert result.data[0]['event_id'] == result.event_id
        assert result.data[0]['farm_name'] == "測試農場"
    
    @pytest.mark.asyncio
    async def test_handle_unknown_file_type(self, temp_db_path: str) -> None:
        handler = UploadCommandHandler(temp_db_path)
        
        # 創建無法識別的Excel文件
        df = pd.DataFrame({
            "無關欄位1": ["測試"],
            "無關欄位2": ["測試"]
        })
        
        excel_buffer = BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        
        mock_file = Mock()
        mock_file.filename = "unknown.xlsx"
        mock_file.read = AsyncMock(return_value=excel_buffer.getvalue())
        
        command = UploadFileCommand(file=mock_file)
        result = await handler.handle(command)
        
        assert result.success is False
        assert result.file_type == "unknown"
        assert "無法識別檔案類型" in result.message
    
    @pytest.mark.asyncio
    async def test_handle_with_exception(self, temp_db_path: str) -> None:
        handler = UploadCommandHandler(temp_db_path)
        
        mock_file = Mock()
        mock_file.filename = "error.xlsx"
        mock_file.read = AsyncMock(side_effect=Exception("讀取文件失敗"))
        
        command = UploadFileCommand(file=mock_file)
        result = await handler.handle(command)
        
        assert result.success is False
        assert "上傳處理失敗" in result.message