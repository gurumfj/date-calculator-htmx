# BreedExporter 呼叫關係圖

## 方法呼叫圖
```mermaid
flowchart TB
    %% 主要入口
    ed["export_data(data)"]
    style ed fill:#f9f,stroke:#333,stroke-width:2px

    %% Session 相關
    subgraph Session操作
        direction TB
        session["Session Context"]
        commit["session.commit()"]
        style session fill:#e1f5fe,stroke:#333
        style commit fill:#e1f5fe,stroke:#333
    end

    %% 主要流程
    ed --> session
    session --> gaek["_get_all_existing_keys()"]
    session --> process["資料處理"]
    process --> commit

    %% 資料處理流程
    subgraph process[資料處理]
        direction TB
        prep["準備資料集合"] --> sync["同步操作"]
        
        subgraph prep[準備資料集合]
            direction LR
            keys["建立唯一識別碼集合"]
            dict["建立記錄字典"]
        end

        subgraph sync[同步操作]
            direction TB
            add["新增資料"] --> del["刪除資料"]
            
            subgraph add[新增資料]
                direction LR
                fkne1["_filter_key_not_exists()"] --> 
                fe1["_for_each()"] -->
                save["_save_data()"] -->
                rto["_record_to_orm()"]
                style fkne1 fill:#98FB98,stroke:#333
                style rto fill:#98FB98,stroke:#333
            end

            subgraph del[刪除資料]
                direction LR
                fkne2["_filter_key_not_exists()"] -->
                fe2["_for_each()"] -->
                delete["_delete_data_by_key()"]
                style fkne2 fill:#98FB98,stroke:#333
            end
        end
    end

    %% 資料庫操作
    subgraph db[資料庫操作]
        direction TB
        select["select()"] 
        add_db["add()"]
        get["get()"]
        del_db["delete()"]
    end

    %% 連接資料庫操作
    gaek --> select
    save --> add_db
    delete --> get
    delete --> del_db

    %% 樣式設定
    classDef primary fill:#f9f,stroke:#333,stroke-width:2px
    classDef secondary fill:#fff,stroke:#333
    classDef db fill:#e1f5fe,stroke:#333
    classDef pure fill:#98FB98,stroke:#333
    
    class ed primary
    class process,prep,sync secondary
    class db db
    class fe1,fe2 pure
```

## 方法層級結構

```mermaid
graph TB
    %% 定義主要方法群組
    subgraph 核心方法["核心方法 (Impure)"]
        ed["export_data()"]
        style ed fill:#f9f,stroke:#333,stroke-width:2px
    end

    subgraph 資料操作方法["資料操作方法 (Impure)"]
        save["_save_data()"]
        delete["_delete_data_by_key()"]
        gaek["_get_all_existing_keys()"]
    end

    subgraph 工具方法["工具方法 (Pure)"]
        fe["_for_each()"]
        fkne["_filter_key_not_exists()"]
        style fe fill:#98FB98,stroke:#333
        style fkne fill:#98FB98,stroke:#333
    end

    subgraph 轉換方法["轉換方法 (Pure)"]
        rto["_record_to_orm()"]
        otr["_orm_to_record()"]
        style rto fill:#98FB98,stroke:#333
        style otr fill:#98FB98,stroke:#333
    end

    %% 定義關係
    ed --> save & delete & gaek
    save --> rto
    delete --> gaek
    ed --> fe & fkne

    %% 樣式
    classDef primary fill:#f9f,stroke:#333,stroke-width:2px
    classDef secondary fill:#fff,stroke:#333
    classDef utility fill:#e1f5fe,stroke:#333
    classDef pure fill:#98FB98,stroke:#333
```

## 主要方法說明

### 函數分類

#### 純函數 (Pure Functions)
具有以下特性的函數：
- 給定相同的輸入，永遠返回相同的輸出
- 不產生副作用（不修改外部狀態）
- 不依賴外部狀態

包含的方法：
- `_for_each`: 純粹的迭代操作
- `_filter_key_not_exists`: 純粹的集合運算
- `_record_to_orm`: 純粹的資料轉換
- `_orm_to_record`: 純粹的資料轉換

#### 非純函數 (Impure Functions)
具有以下特性的函數：
- 可能產生副作用（如資料庫操作、日誌記錄）
- 結果可能依賴外部狀態
- 相同輸入可能產生不同輸出

包含的方法：
- `export_data`: 執行資料庫操作
- `_save_data`: 修改資料庫狀態
- `_delete_data_by_key`: 修改資料庫狀態
- `_get_all_existing_keys`: 依賴資料庫狀態

### 核心方法
- `export_data`: 主要入口點，協調所有資料同步操作
  - 參數: `data: ProcessingResult[BreedRecord]`
  - 回傳: `None`
  - 類型: 非純函數（涉及資料庫操作）

### 資料操作方法
- `_save_data`: 儲存單筆記錄（非純函數）
- `_delete_data_by_key`: 刪除指定識別碼的記錄（非純函數）
- `_get_all_existing_keys`: 取得所有現有識別碼（非純函數）

### 工具方法
- `_for_each`: 通用迭代器（純函數）
- `_filter_key_not_exists`: 過濾不存在的識別碼（純函數）

### 轉換方法
- `_record_to_orm`: 資料模型轉換（純函數）
- `_orm_to_record`: 資料模型轉換（純函數）

## 呼叫關係特點

1. **單一職責**
   - 每個方法都有明確的功能
   - 轉換邏輯與資料操作分離

2. **層級結構**
   - 核心方法協調整體流程
   - 工具方法提供通用功能
   - 資料操作方法處理具體邏輯

3. **資料流向**
   - 資料同步雙向操作（新增/刪除）
   - 清晰的資料轉換路徑
   - 集中的交易管理

4. **純函數與非純函數分離**
   - 純函數負責資料轉換和工具操作
   - 非純函數處理資料庫操作和狀態管理
   - 清晰的職責分離有助於測試和維護