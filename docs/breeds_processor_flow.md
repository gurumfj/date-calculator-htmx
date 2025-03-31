# 資料處理與匯出流程文件

## 1. 類別關係圖

```mermaid
classDiagram
    class IProcessor~T~ {
        <<interface>>
        +process_data(data: DataFrame) ProcessingResult~T~
    }

    class IExporter~T~ {
        <<interface>>
        +export_data(data: ProcessingResult~T~)
        +export_errors(data: ProcessingResult~T~)
    }

    class BreedsProcessor {
        +process_data(data: DataFrame) ProcessingResult~BreedRecord~
    }

    class BreedSQLiteExporter {
        +export_data(data: ProcessingResult~BreedRecord~)
        +export_errors(data: ProcessingResult~BreedRecord~)
        -_init_database()
        -save_data(session, record)
        -delete_data_by_key(session, key)
    }

    class ProcessingResult~T~ {
        +processed_data: List~T~
        +errors: List~ErrorMessage~
    }

    IProcessor <|.. BreedsProcessor
    IExporter <|.. BreedSQLiteExporter
    BreedsProcessor ..> ProcessingResult : creates
    BreedSQLiteExporter ..> ProcessingResult : consumes
```

## 2. 資料匯出時序圖

```mermaid
sequenceDiagram
    participant Client
    participant Exporter as BreedSQLiteExporter
    participant DB as SQLite Database

    Client->>Exporter: export_data(ProcessingResult)
    activate Exporter

    Exporter->>DB: get_all_existing_keys()
    DB-->>Exporter: existing_keys

    Note over Exporter: Compare keys to determine<br/>updates and deletions

    loop For new/updated records
        Exporter->>Exporter: record_to_orm(record)
        Exporter->>DB: save_data(record)
    end

    loop For deleted records
        Exporter->>DB: delete_data_by_key(key)
    end

    Exporter->>DB: commit transaction
    Exporter-->>Client: void
    deactivate Exporter
```

## 3. 資料匯出流程圖

```mermaid
flowchart TD
    A[ProcessingResult] --> B[Get Existing Keys]
    B --> C[Compare Keys]

    C --> D[New Records]
    C --> E[Records to Delete]

    D --> F[Convert to ORM]
    F --> G[Save to Database]

    E --> H[Delete from Database]

    G --> I[Commit Changes]
    H --> I
```

## 4. 資料轉換與持久化

### BreedRecordORM 模型
```python
class BreedRecordORM(SQLModel, table=True):
    unique_id: str  # Primary Key
    farm_name: str | None
    # ... 其他欄位 ...
```

### 核心方法職責
1. **export_data**
   - 輸入：ProcessingResult<BreedRecord>
   - 處理：比對現有資料，執行新增/刪除操作
   - 輸出：void

2. **save_data**
   - 輸入：Session, BreedRecord
   - 處理：轉換並儲存記錄
   - 輸出：void

3. **delete_data_by_key**
   - 輸入：Session, str (unique_id)
   - 處理：刪除指定記錄
   - 輸出：void

## 5. 資料同步策略

1. **新增/更新策略**
   - 取得所有現有記錄的 unique_id
   - 比對新資料集的 unique_id
   - 對不存在的記錄執行新增操作

2. **刪除策略**
   - 找出資料庫中存在但新資料集中不存在的記錄
   - 執行刪除操作

3. **事務處理**
   - 使用 SQLAlchemy Session 確保事務完整性
   - 所有操作在同一事務中完成

## 使用範例

```python
# 建立匯出器實例
exporter = BreedSQLiteExporter("database.sqlite")

# 處理資料
processor = BreedsProcessor()
result = processor.process_data(df)

# 匯出資料
exporter.export_data(result)
