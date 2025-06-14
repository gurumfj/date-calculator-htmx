from __future__ import annotations

import pytest
import tempfile
import os
from typing import Generator

from cleansales_backend.queries.data_queries import (
    DataQueryHandler,
    GetDataQuery,
    GetUploadEventsQuery,
    GetEventDetailsQuery
)


class TestDataQueryHandler:
    @pytest.fixture
    def temp_db_path(self) -> Generator[str, None, None]:
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        from cleansales_backend.database.init import init_db
        init_db(db_path)
        
        yield db_path
        os.unlink(db_path)
    
    @pytest.fixture
    def sample_data(self, temp_db_path: str) -> DataQueryHandler:
        """插入測試數據"""
        handler = DataQueryHandler(temp_db_path)
        conn = handler.get_db_connection()
        
        # 插入breed測試數據
        conn.execute("""
            INSERT INTO breed (
                unique_id, farm_name, batch_name, chicken_breed, breed_date,
                breed_male, breed_female, event_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'test001', '測試農場A', 'BATCH001', '白肉雞', '2024-01-01',
            100, 200, 'event-001'
        ))
        
        conn.execute("""
            INSERT INTO breed (
                unique_id, farm_name, batch_name, chicken_breed, breed_date,
                breed_male, breed_female, event_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'test002', '測試農場B', 'BATCH002', '土雞', '2024-01-02',
            150, 250, 'event-002'
        ))
        
        # 插入upload_events測試數據
        conn.execute("""
            INSERT INTO upload_events (
                event_id, file_type, file_name, file_size, processing_status,
                valid_count, invalid_count, inserted_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'event-001', 'breed', 'test1.xlsx', 1000, 'completed',
            1, 0, 1
        ))
        
        conn.execute("""
            INSERT INTO upload_events (
                event_id, file_type, file_name, file_size, processing_status,
                valid_count, invalid_count, inserted_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'event-002', 'breed', 'test2.xlsx', 2000, 'completed',
            1, 0, 1
        ))
        
        conn.commit()
        conn.close()
        
        return handler
    
    def test_handle_get_data_query_all_breeds(self, sample_data: DataQueryHandler) -> None:
        handler = sample_data
        query = GetDataQuery(table_name="breed")
        
        results = handler.handle_get_data_query(query)
        
        assert len(results) == 2
        assert results[0]['farm_name'] == '測試農場B'  # 按breed_date DESC排序
        assert results[1]['farm_name'] == '測試農場A'
    
    def test_handle_get_data_query_with_column_order(self, sample_data: DataQueryHandler) -> None:
        handler = sample_data
        query = GetDataQuery(table_name="breed", column="farm_name", order="ASC")
        
        results = handler.handle_get_data_query(query)
        
        assert len(results) == 2
        assert results[0]['farm_name'] == '測試農場A'  # 按farm_name ASC排序
        assert results[1]['farm_name'] == '測試農場B'
    
    def test_handle_get_data_query_with_event_id_filter(self, sample_data: DataQueryHandler) -> None:
        handler = sample_data
        query = GetDataQuery(table_name="breed", event_id="event-001")
        
        results = handler.handle_get_data_query(query)
        
        assert len(results) == 1
        assert results[0]['farm_name'] == '測試農場A'
        assert results[0]['event_id'] == 'event-001'
    
    def test_handle_get_data_query_with_limit(self, sample_data: DataQueryHandler) -> None:
        handler = sample_data
        query = GetDataQuery(table_name="breed", limit=1)
        
        results = handler.handle_get_data_query(query)
        
        assert len(results) == 1
        assert results[0]['farm_name'] == '測試農場B'  # 最新的記錄
    
    def test_handle_get_upload_events_query(self, sample_data: DataQueryHandler) -> None:
        handler = sample_data
        query = GetUploadEventsQuery(limit=100)
        
        results = handler.handle_get_upload_events_query(query)
        
        assert len(results) == 2
        assert results[0]['event_id'] == 'event-001'  # 按時間戳DESC排序
        assert results[1]['event_id'] == 'event-002'
    
    def test_handle_get_upload_events_query_with_limit(self, sample_data: DataQueryHandler) -> None:
        handler = sample_data
        query = GetUploadEventsQuery(limit=1)
        
        results = handler.handle_get_upload_events_query(query)
        
        assert len(results) == 1
        assert results[0]['event_id'] == 'event-001'  # 最新的事件
    
    def test_handle_get_event_details_query_existing(self, sample_data: DataQueryHandler) -> None:
        handler = sample_data
        query = GetEventDetailsQuery(event_id="event-001")
        
        result = handler.handle_get_event_details_query(query)
        
        assert result is not None
        assert result['file_type'] == 'breed'
        assert result['file_name'] == 'test1.xlsx'
        assert result['processing_status'] == 'completed'
    
    def test_handle_get_event_details_query_non_existing(self, sample_data: DataQueryHandler) -> None:
        handler = sample_data
        query = GetEventDetailsQuery(event_id="non-existing")
        
        result = handler.handle_get_event_details_query(query)
        
        assert result is None
    
    def test_get_batch_statistics(self, sample_data: DataQueryHandler) -> None:
        handler = sample_data
        
        results, total_count = handler.get_batch_statistics()
        
        assert len(results) == 2
        assert total_count == 2
        # 驗證批次統計數據結構
        for result in results:
            assert 'batch_name' in result
            assert 'chicken_breed' in result
            assert 'male' in result
            assert 'female' in result
            assert 'breed_date' in result
            assert 'expire_date' in result
            assert 'count' in result
    
    def test_get_batch_statistics_with_completed_batches(self, temp_db_path: str) -> None:
        handler = DataQueryHandler(temp_db_path)
        conn = handler.get_db_connection()
        
        # 插入已完成的批次（應該被過濾掉）
        conn.execute("""
            INSERT INTO breed (
                unique_id, farm_name, batch_name, chicken_breed, breed_date,
                breed_male, breed_female, is_completed, event_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'test003', '測試農場C', 'BATCH003', '白肉雞', '2024-01-03',
            100, 200, 1, 'event-003'  # is_completed = 1
        ))
        
        conn.commit()
        conn.close()
        
        results, total_count = handler.get_batch_statistics()
        
        # 應該不包含已完成的批次
        batch_names = [r['batch_name'] for r in results]
        assert 'BATCH003' not in batch_names
        assert total_count == 0  # 沒有未完成的批次
    
    def test_get_batch_statistics_with_limit(self, sample_data: DataQueryHandler) -> None:
        handler = sample_data
        
        # 測試limit參數
        results, total_count = handler.get_batch_statistics(limit=1)
        
        assert len(results) == 1
        assert total_count == 2  # 總數仍然是2
        # 驗證返回的是按expire_date DESC排序的第一個
        assert results[0]['batch_name'] in ['BATCH001', 'BATCH002']
    
    def test_get_batch_statistics_with_offset(self, sample_data: DataQueryHandler) -> None:
        handler = sample_data
        
        # 測試offset參數
        results, total_count = handler.get_batch_statistics(limit=1, offset=1)
        
        assert len(results) == 1
        assert total_count == 2
        # 驗證返回的是第二個記錄
        assert results[0]['batch_name'] in ['BATCH001', 'BATCH002']
    
    def test_get_batch_statistics_pagination(self, temp_db_path: str) -> None:
        # 創建更多測試數據來測試分頁
        handler = DataQueryHandler(temp_db_path)
        conn = handler.get_db_connection()
        
        # 插入多個批次
        for i in range(5):
            conn.execute("""
                INSERT INTO breed (
                    unique_id, farm_name, batch_name, chicken_breed, breed_date,
                    breed_male, breed_female, is_completed, event_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                f'test{i:03d}', f'測試農場{i}', f'BATCH{i:03d}', '白肉雞', f'2024-01-{i+1:02d}',
                100 + i * 10, 200 + i * 10, 0, f'event-{i:03d}'
            ))
        
        conn.commit()
        conn.close()
        
        # 測試第一頁
        results_page1, total_count = handler.get_batch_statistics(limit=2, offset=0)
        assert len(results_page1) == 2
        assert total_count == 5
        
        # 測試第二頁
        results_page2, total_count = handler.get_batch_statistics(limit=2, offset=2)
        assert len(results_page2) == 2
        assert total_count == 5
        
        # 測試最後一頁
        results_page3, total_count = handler.get_batch_statistics(limit=2, offset=4)
        assert len(results_page3) == 1  # 只剩一個記錄
        assert total_count == 5
        
        # 驗證沒有重複的batch_name
        all_batch_names = [r['batch_name'] for r in results_page1 + results_page2 + results_page3]
        assert len(set(all_batch_names)) == 5  # 5個不同的batch_name