# SalesProcessor 資料流程分析

## 核心類型定義

```typescript
# 基礎類型
GroupID: TypeAlias = int
PreRecords: TypeAlias = tuple[SaleRecordUpdate, ...]
GroupedRecords: TypeAlias = tuple[SaleRecordUpdate, ...]
ProcessedRecords: TypeAlias = tuple[SaleRecordUpdate, ...]

# 泛型參數
T = TypeVar("T")  # 輸入類型
R = TypeVar("R")  # 返回類型
```

## 數據轉換流程

```mermaid
flowchart TD
    A[DataFrame] -->|sort_values| B[排序數據]
    B -->|reduce| C[驗證與清理]

    subgraph validation[數據驗證]
        C -->|model_validate| D[ValidatorSchema]
        D -->|create_from| E[SaleRecordUpdate]
    end

    E -->|ProcessingState| F[初始狀態]

    subgraph processing[群組處理]
        F -->|reduce| G[處理每筆記錄]
        G -->|add_to_group| H[加入群組]
        H -->|should_create_new_group| I{需要新群組?}
        I -->|是| J[assign_group_key]
        I -->|否| G
        J -->|process_current_group| G
    end

    processing -->|ProcessingResult| K[最終結果]
```

## 函數式工具集

```mermaid
classDiagram
    class SaleUtil {
        <<static>>
        +map_tuple(data: tuple[T], func: Callable[[T], R]) tuple[R]
        +filter_tuple(data: tuple[T], predicate: Callable[[T], bool]) tuple[T]
        +reduce_tuple(data: tuple[T], func: Callable[[R, T], R], initial: R) R
        +catch_error(callback: Callable, error_callback: Callable) T
    }
```

## 不可變數據結構

```mermaid
classDiagram
    class SaleRecordUpdate {
        <<frozen>>
        +create_from(data: Union[dict, SaleRecord, ValidatorSchema]) SaleRecordUpdate
        +with_updates(**updates: Any) SaleRecordUpdate
    }

    class ProcessingState {
        <<frozen>>
        +processed_records: ProcessedRecords
        +grouped_records: GroupedRecords
        +group_id: GroupID
        +cleaned_records: PreRecords
        +add_to_group(record: SaleRecordUpdate) ProcessingState
        +process_current_group(group: ProcessedRecords) ProcessingState
    }
```

## 群組處理邏輯

```mermaid
stateDiagram-v2
    [*] --> 檢查記錄

    state 群組判斷 {
        檢查記錄 --> 位置檢查
        位置檢查 --> 日期檢查: 相同位置

        位置檢查 --> 建立新群組: 位置不同
        日期檢查 --> 建立新群組: 差異>45天
        日期檢查 --> 保持群組: 差異<=45天
    }

    建立新群組 --> 更新位置
    保持群組 --> [*]
    更新位置 --> [*]
```

## 日誌層級

```mermaid
flowchart TD
    A[DEBUG] -->|位置變更| B[位置改變記錄]
    A -->|日期差異| C[日期差異記錄]
    A -->|群組鍵值| D[鍵值生成記錄]

    E[INFO] -->|處理完成| F[記錄數統計]
    E -->|清理完成| G[有效記錄統計]

    H[WARNING] -->|驗證失敗| I[錯誤記錄統計]
```

## 核心處理步驟

1. **數據驗證與清理**
   ```python
   def _validate_and_clean_records(data: pd.DataFrame) -> tuple[PreRecords, list[ErrorMessage]]:
       sorted_data = data.sort_values(by=["場別", "日期"])
       return reduce(process_row, sorted_data.iterrows(), ((), []))
   ```

2. **群組處理**
   ```python
   def _process_group_and_assign_keys(
       state: ProcessingState,
       record_with_idx: tuple[int, SaleRecordUpdate]
   ) -> ProcessingState:
       # 加入群組
       new_state = state.add_to_group(record)

       # 處理群組
       if should_process_group:
           processed_group = _assign_group_key_to_location(new_state.grouped_records)
           return new_state.process_current_group(processed_group)
   ```

3. **位置鍵值生成**
   ```python
   def _assign_group_key_to_location(group: tuple[SaleRecordUpdate, ...]) -> tuple[SaleRecordUpdate, ...]:
       median_date = _calculate_date_median(max_date, min_date)
       return SaleUtil.map_tuple(group, lambda r: r.with_updates(location=new_key))
   ```

## 不可變性保證

1. **資料結構**
   - 使用 `@dataclass(frozen=True)` 確保實例不可變
   - 所有集合使用 `tuple` 而非 `list`
   - 狀態更新通過 `replace` 創建新實例

2. **函數式操作**
   - 使用 `reduce` 進行狀態轉換
   - 通過 `map_tuple` 進行批量更新
   - 純函數設計，無副作用

3. **錯誤處理**
   - 使用 `catch_error` 包裝可能的異常
   - 錯誤信息通過 `ErrorMessage` 封裝
   - 日誌記錄錯誤但不影響流程
