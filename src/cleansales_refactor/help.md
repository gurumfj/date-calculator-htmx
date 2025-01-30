# SaleRecordProcessor 處理流程

```mermaid
graph TD
    %% 主要入口
    Start([開始]) --> Process[SalesProcessor.process_data]
    Process --> SortData[資料排序by日期]
    Process --> End([結束])

    %% 主要處理階段
    subgraph "1. 資料驗證清理"
        SortData --> Validate[_validate_and_clean_records]
        Validate --> Schema[SaleRecordValidatorSchema.model_validate]
        Schema --> Convert[SalesDtoProcessor.validator_schema_to_dataclass]
        Convert --> ValidateResult{有效記錄?}
        ValidateResult -->|否| EmptyResult[回傳空結果]
        ValidateResult -->|是| ContinueProcess[繼續處理]
    end

    %% 分組處理
    subgraph "2. 位置分組"
        ContinueProcess --> ListCopy1[SaleUtil.with_list_copy]
        ListCopy1 --> GroupLocation[SalesDtoProcessor.group_by_location]
        GroupLocation --> GroupField[_group_by_field]
    end

    %% 群組處理
    subgraph "3. 群組處理"
        GroupField --> DictCopy[SaleUtil.with_dict_copy]
        DictCopy --> ProcessGroups[_process_groups]
        ProcessGroups --> ListCopy2[SaleUtil.with_list_copy]
        ListCopy2 --> DateDiff[_calculate_date_diff_and_assign_group_id]
        DateDiff --> AssignDateDiff[SaleUtil.assign_date_diff]
        DateDiff --> AssignGroupId[SaleUtil.assign_group_id]
        DateDiff --> AssignGroupKey[_assign_group_key_to_location]
        AssignGroupKey --> CalcMedian[SaleUtil.calculate_date_median]
    end

    %% 結果轉換
    subgraph "4. 結果轉換"
        ProcessGroups --> ToResult[SalesDtoProcessor.salesgroups_to_processingresult]
        ToResult --> FinalResult[ProcessingResult]
    end

    classDef default fill:#f9f,stroke:#333,stroke-width:2px
    classDef process fill:#bbf,stroke:#333,stroke-width:1px
    classDef condition fill:#ffd,stroke:#333,stroke-width:1px
    classDef startEnd fill:#9f9,stroke:#333,stroke-width:2px
    classDef util fill:#dfd,stroke:#333,stroke-width:1px
    classDef copy fill:#fef,stroke:#333,stroke-width:1px

    class Start,End startEnd
    class Process,GroupLocation,ProcessGroups default
    class Validate,Convert,GroupField,DateDiff,AssignGroupKey process
    class ValidateResult condition
    class AssignDateDiff,AssignGroupId,CalcMedian util
    class ListCopy1,ListCopy2,DictCopy copy
```

## 類別職責說明

### SalesProcessor
主要的處理邏輯類別，負責協調整個處理流程。
- 資料預處理（排序）
- 資料驗證與清理
- 群組處理協調

### SalesDtoProcessor
資料轉換和分組處理的工具類別。主要負責：
- Schema 到 Dataclass 的轉換
- 記錄分組邏輯
- 結果轉換

### SaleUtil
通用工具類別，提供：
- 資料複製包裝（with_dict_copy, with_list_copy）
- 日期差異計算
- 群組 ID 分配
- 日期中位數計算

## 主要處理流程

1. **資料驗證與清理**
   - 資料預排序
   - 輸入驗證
   - Schema 轉換
   - 錯誤收集

2. **位置分組**
   - 資料複製保護
   - 依據位置進行初步分組
   - 使用通用分組函數

3. **群組處理**
   - 資料複製保護
   - 日期差異計算
   - 群組 ID 分配
   - 群組鍵生成

4. **結果轉換**
   - 轉換為最終的 ProcessingResult 格式
   - 包含分組資料和錯誤訊息