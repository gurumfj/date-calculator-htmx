SELECT 
    event_id, file_type, file_name, file_size, upload_timestamp,
    processing_status, valid_count, invalid_count, duplicates_removed,
    inserted_count, deleted_count, duplicate_count, error_message,
    processing_time_ms
FROM upload_events 
ORDER BY upload_timestamp DESC
LIMIT :limit