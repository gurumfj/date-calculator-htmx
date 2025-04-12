import { RefObject } from "react";
import type { Database } from "@app-types";

// 定義資料表類型
export type TableName = keyof Database["public"]["Tables"];

// 通用查詢選項
export interface QueryOptions {
  eq?: Record<string, any>;
  gt?: Record<string, any>;
  lt?: Record<string, any>;
  gte?: Record<string, any>;
  lte?: Record<string, any>;
  like?: Record<string, any>;
  ilike?: Record<string, any>;
  in?: Record<string, any>;
  neq?: Record<string, any>;
  limit?: number;
  offset?: number;
  order?: {
    column: string;
    ascending?: boolean;
  };
}

// 操作結果介面
export interface OperationResult<T> {
  data: T | null;
  error: Error | null;
}

// 批量操作結果介面
export interface ListOperationResult<T> {
  data: T[] | null;
  error: Error | null;
}

// 刪除操作結果介面
export interface DeleteOperationResult {
  error: Error | null;
}

// useSupabase hook 回傳值的介面
export interface UseSupabaseReturn<T> {
  data: T[] | null;
  error: Error | null;
  loading: boolean;
  refetch: () => Promise<void>;
  insert: (record: Partial<T>) => Promise<OperationResult<T>>;
  update: (
    id: string,
    record: Partial<T>,
    idField?: string
  ) => Promise<OperationResult<T>>;
  remove: (id: string, idField?: string) => Promise<DeleteOperationResult>;
}

// 內部狀態追蹤
export interface SupabaseHookState<T> {
  data: T[] | null;
  error: Error | null;
  loading: boolean;
  isMounted: RefObject<boolean>;
  lastOptionsString: RefObject<string>;
  initialFetchDone: RefObject<boolean>;
}
