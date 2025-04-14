import { useState, useEffect, useCallback, useRef } from "react";
import supabase from "@app-lib/supabaseClient";
import {
  TableName,
  QueryOptions,
  UseSupabaseReturn,
  OperationResult,
  DeleteOperationResult,
} from "./types";
import { buildQuery, hasOptionsChanged } from "./queryBuilder";
import {
  fetchData,
  insertRecord,
  updateRecord,
  removeRecord,
} from "./crudOperations";
import {
  updateHookState,
  updateStateAfterInsert,
  updateStateAfterUpdate,
  updateStateAfterRemove,
} from "./stateManager";

/**
 * useSupabase hook - 用於與Supabase資料表進行交互
 * @param table 要查詢的資料表名
 * @param options 查詢選項，包括過濾、排序、分頁等
 * @param idField 主鍵欄位名，預設為'unique_id'
 * @param autoFetch 是否在組件掛載時自動查詢資料，預設為true
 * @returns 包含資料、狀態和CRUD操作方法的物件
 */
export function useSupabase<T>(
  table: TableName,
  options: QueryOptions = {},
  idField: string = "unique_id",
  autoFetch: boolean = true
): UseSupabaseReturn<T> {
  const [data, setData] = useState<T[] | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [loading, setLoading] = useState<boolean>(autoFetch);

  // 使用 ref 追蹤狀態
  const isMounted = useRef(true);
  const lastOptionsString = useRef("");
  const initialFetchDone = useRef(false);

  // 檢查查詢選項是否發生變化
  const optionsChanged = useCallback(() => {
    const [changed, newOptionsString] = hasOptionsChanged(
      options,
      lastOptionsString.current
    );
    if (changed) {
      lastOptionsString.current = newOptionsString;
    }
    return changed;
  }, [options]);

  // 查詢資料
  const fetchDataFromTable = useCallback(async () => {
    // 如果組件已經卸載，不執行查詢
    if (!isMounted.current) return;

    try {
      updateHookState<T>(
        {
          data,
          error,
          loading,
          isMounted,
          lastOptionsString,
          initialFetchDone,
        },
        setData,
        setError,
        setLoading,
        true,
        null
      );

      console.log(`Fetching data from ${String(table)}...`);

      const query = buildQuery(supabase, table, options);
      const result = await fetchData<T>(supabase, query);

      if (result.error) {
        throw result.error;
      }

      // 確保組件仍然掛載再設置狀態
      if (isMounted.current) {
        console.log(`Data fetched from ${String(table)}:`, result.data);

        updateHookState<T>(
          {
            data,
            error,
            loading,
            isMounted,
            lastOptionsString,
            initialFetchDone,
          },
          setData,
          setError,
          setLoading,
          false,
          null,
          result.data
        );

        initialFetchDone.current = true;
      }
    } catch (err) {
      console.error(`Error fetching data from ${String(table)}:`, err);

      if (isMounted.current) {
        const errorObj = err instanceof Error ? err : new Error(String(err));

        updateHookState<T>(
          {
            data,
            error,
            loading,
            isMounted,
            lastOptionsString,
            initialFetchDone,
          },
          setData,
          setError,
          setLoading,
          false,
          errorObj
        );

        initialFetchDone.current = true;
      }
    } finally {
      if (isMounted.current) {
        setLoading(false);
      }
    }
  }, [table, options, data, error, loading]);

  // 添加記錄
  const insert = useCallback(
    async (record: Partial<T>): Promise<OperationResult<T>> => {
      const result = await insertRecord<T>(supabase, table, record, idField);

      if (result.data && isMounted.current) {
        updateStateAfterInsert<T>(
          {
            data,
            error,
            loading,
            isMounted,
            lastOptionsString,
            initialFetchDone,
          },
          setData,
          result.data
        );
      }

      return result;
    },
    [table, idField, data, error, loading]
  );

  // 更新記錄
  const update = useCallback(
    async (
      id: string,
      record: Partial<T>,
      customIdField?: string
    ): Promise<OperationResult<T>> => {
      const fieldToUse = customIdField || idField;
      const result = await updateRecord<T>(
        supabase,
        table,
        id,
        record,
        fieldToUse
      );

      if (result.data && isMounted.current) {
        updateStateAfterUpdate<T>(
          {
            data,
            error,
            loading,
            isMounted,
            lastOptionsString,
            initialFetchDone,
          },
          setData,
          id,
          result.data,
          fieldToUse
        );
      }

      return result;
    },
    [table, idField, data, error, loading]
  );

  // 刪除記錄
  const remove = useCallback(
    async (
      id: string,
      customIdField?: string
    ): Promise<DeleteOperationResult> => {
      const fieldToUse = customIdField || idField;
      const result = await removeRecord(supabase, table, id, fieldToUse);

      if (!result.error && isMounted.current) {
        updateStateAfterRemove<T>(
          {
            data,
            error,
            loading,
            isMounted,
            lastOptionsString,
            initialFetchDone,
          },
          setData,
          id,
          fieldToUse
        );
      }

      return result;
    },
    [table, idField, data, error, loading]
  );

  // 初始化和選項變更時獲取數據
  useEffect(() => {
    // 根據 autoFetch 設置初始加載狀態
    if (autoFetch && !initialFetchDone.current) {
      console.log(`Initial fetch for ${String(table)} starting...`);
      fetchDataFromTable();
    } else if (!autoFetch) {
      // 如果不自動獲取，確保不處於加載狀態
      setLoading(false);
    }
  }, [autoFetch, fetchDataFromTable, table]);

  // 查詢選項變化時重新獲取數據
  useEffect(() => {
    if (initialFetchDone.current && autoFetch && optionsChanged()) {
      console.log(`Options changed for ${String(table)}, refetching...`);
      fetchDataFromTable();
    }
  }, [autoFetch, fetchDataFromTable, optionsChanged, table]);

  // 組件卸載處理
  useEffect(() => {
    return () => {
      console.log(`Component using ${String(table)} hook unmounting...`);
      isMounted.current = false;
      setLoading(false);
    };
  }, [table]);

  return {
    data,
    error,
    loading,
    refetch: fetchDataFromTable,
    insert,
    update,
    remove,
  };
}

export default useSupabase;
