SELECT file_type, file_name, upload_timestamp, processing_status,
       inserted_count, deleted_count, duplicate_count
FROM upload_events 
WHERE event_id = :event_id