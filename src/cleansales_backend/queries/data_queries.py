from __future__ import annotations

import logging
import math
import sqlite3
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class GetDataQuery:
    table_name: str
    sort_by_column: str | None = None
    sort_order: str | None = None
    event_id: str | None = None
    pagination: PaginationQuery | None = None

@dataclass
class PaginationQuery:
    page: int
    page_size: int


@dataclass
class GetUploadEventsQuery:
    limit: int = 100


@dataclass
class GetEventDetailsQuery:
    event_id: str


class DataQueryHandler:
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def get_db_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def handle_get_data_query(self, query: GetDataQuery) -> tuple[list[dict[str, Any]], int]:
        """
        Handle GetDataQuery and return a tuple of list of dictionaries and total pages.
        
        The first element of the tuple is a list of dictionaries, each dictionary represents a row 
        in the table specified by the GetDataQuery's table_name attribute.
        The second element is the total number of pages.
        
        The results are paginated if GetDataQuery's pagination attribute is not None.
        The order of the results are determined by GetDataQuery's sort_by_column and sort_order attributes.
        If sort_by_column is not specified, the results are sorted by the column specified by the table_name attribute:
        - breed: breed_date DESC
        - sale: sale_date DESC
        - feed: feed_date DESC
        
        If GetDataQuery's event_id attribute is not None, the results are filtered by event_id = ?.
        
        The total number of pages is calculated by the total number of records divided by the page size.
        If the total number of pages is 0, -1 is returned instead.
        """
        
        conn = self.get_db_connection()
        try:
            base_sql = f"SELECT * FROM {query.table_name}"
            count_sql = f"SELECT COUNT(*) FROM {query.table_name}"
            conditions = []
            params = []
            
            if query.event_id:
                conditions.append("event_id = ?")
                params.append(query.event_id)
            
            if conditions:
                base_sql += " WHERE " + " AND ".join(conditions)
                count_sql += " WHERE " + " AND ".join(conditions)
            
            if query.sort_by_column:
                base_sql += f" ORDER BY {query.sort_by_column} {query.sort_order or 'DESC'}"
            else:
                if query.table_name == "breed":
                    base_sql += " ORDER BY breed_date DESC"
                elif query.table_name == "sale":
                    base_sql += " ORDER BY sale_date DESC"
                elif query.table_name == "feed":
                    base_sql += " ORDER BY feed_date DESC"

            total_pages = -1
            if query.pagination:
                # Get count first with condition params only
                count_params = [p for p in params]  # Copy condition params
                count = conn.execute(count_sql, count_params).fetchone()[0]
                total_pages = math.ceil(count / query.pagination.page_size)

                
                # Add pagination params to main query
                offset = (query.pagination.page - 1) * query.pagination.page_size
                base_sql += " LIMIT ? OFFSET ?"
                params.extend([query.pagination.page_size, offset])
            print(base_sql, params)
            cursor = conn.execute(base_sql, params)
            results = cursor.fetchall()
            print(len(results))
            return [dict(row) for row in results], total_pages
        finally:
            conn.close()
    
    def handle_get_upload_events_query(self, query: GetUploadEventsQuery) -> list[dict[str, Any]]:
        conn = self.get_db_connection()
        try:
            cursor = conn.execute("""
                SELECT 
                    event_id, file_type, file_name, file_size, upload_timestamp,
                    processing_status, valid_count, invalid_count, duplicates_removed,
                    inserted_count, deleted_count, duplicate_count, error_message,
                    processing_time_ms
                FROM upload_events 
                ORDER BY upload_timestamp DESC
                LIMIT ?
            """, (query.limit,))
            results = cursor.fetchall()
            return [dict(row) for row in results]
        finally:
            conn.close()
    
    def handle_get_event_details_query(self, query: GetEventDetailsQuery) -> dict[str, Any] | None:
        conn = self.get_db_connection()
        try:
            cursor = conn.execute("""
                SELECT file_type, file_name, upload_timestamp, processing_status,
                       inserted_count, deleted_count, duplicate_count
                FROM upload_events 
                WHERE event_id = ?
            """, (query.event_id,))
            result = cursor.fetchone()
            return dict(result) if result else None
        finally:
            conn.close()
    
    def get_batch_statistics(self, limit: int = 100, offset: int = 0) -> tuple[list[dict[str, Any]], int]:
        conn = self.get_db_connection()
        try:
            # 使用簡單的方法：先獲取所有數據，然後在 Python 中處理分頁
            cursor = conn.execute("""
                SELECT 
                    batch_name, chicken_breed,
                    SUM(breed_male) AS male,
                    SUM(breed_female) AS female,
                    MIN(breed_date) AS breed_date,
                    DATE(breed_date, '+120 days') AS expire_date,
                    COUNT(batch_name) AS count
                FROM breed 
                WHERE is_completed = 0 
                GROUP BY batch_name 
                ORDER BY expire_date DESC
            """)
            
            all_results = cursor.fetchall()
            total_count = len(all_results)
            
            # 在 Python 中處理分頁
            start_idx = offset
            end_idx = offset + limit
            paginated_results = all_results[start_idx:end_idx]
            
            records = [dict(row) for row in paginated_results]
            return records, total_count
        finally:
            conn.close()