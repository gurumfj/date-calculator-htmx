import { SupabaseClient } from "@supabase/supabase-js";
import {
  TableName,
  OperationResult,
  DeleteOperationResult,
  ListOperationResult,
} from "./types";

/**
 * 從資料表讀取資料
 * @param supabase Supabase 客戶端實例
 * @param query 已構建的查詢物件
 * @returns 查詢結果和可能的錯誤
 */
export const fetchData = async <T>(
  _supabase: SupabaseClient, // 添加底線前綴表示此參數不會被使用
  query: any // 使用更通用的類型
): Promise<ListOperationResult<T>> => {
  try {
    const result = await query;

    if (result.error) {
      throw result.error;
    }

    return { data: result.data as T[], error: null };
  } catch (err) {
    console.error(`Error fetching data:`, err);
    const error = err instanceof Error ? err : new Error(String(err));
    return { data: null, error };
  }
};

/**
 * 新增記錄到資料表
 * @param supabase Supabase 客戶端實例
 * @param table 資料表名
 * @param record 要新增的記錄
 * @param idField 主鍵欄位名
 * @returns 新增結果和可能的錯誤
 */
export const insertRecord = async <T>(
  supabase: SupabaseClient,
  table: TableName,
  record: Partial<T>,
  idField: string = "unique_id"
): Promise<OperationResult<T>> => {
  try {
    const now = new Date().toISOString();

    // 準備新記錄
    let newRecord: any = {
      ...record,
      updated_at: now,
    };

    // 如果沒有主鍵值，則自動生成
    if (record[idField as keyof typeof record] === undefined) {
      newRecord[String(idField)] = `${String(table)}-${Date.now()}`;
    }

    console.log(`Inserting record to ${table}:`, newRecord);

    const { data, error } = await supabase
      .from(table)
      .insert(newRecord)
      .select()
      .single();

    if (error) {
      throw error;
    }

    console.log(`Record inserted to ${table}:`, data);

    return { data: data as T, error: null };
  } catch (err) {
    console.error(`Error inserting data into ${table}:`, err);
    const error = err instanceof Error ? err : new Error(String(err));
    return { data: null, error };
  }
};

/**
 * 更新資料表中的記錄
 * @param supabase Supabase 客戶端實例
 * @param table 資料表名
 * @param id 記錄ID
 * @param record 要更新的欄位和值
 * @param idField 主鍵欄位名
 * @returns 更新結果和可能的錯誤
 */
export const updateRecord = async <T>(
  supabase: SupabaseClient,
  table: TableName,
  id: string,
  record: Partial<T>,
  idField: string = "unique_id"
): Promise<OperationResult<T>> => {
  try {
    console.log(`Updating record in ${table} with ${idField}=${id}:`, record);

    const { data, error } = await supabase
      .from(table)
      .update({
        ...record,
        updated_at: new Date().toISOString(),
      })
      .eq(idField, id)
      .select()
      .single();

    if (error) {
      throw error;
    }

    console.log(`Record updated in ${table}:`, data);

    return { data: data as T, error: null };
  } catch (err) {
    console.error(`Error updating data in ${table}:`, err);
    const error = err instanceof Error ? err : new Error(String(err));
    return { data: null, error };
  }
};

/**
 * 從資料表刪除記錄
 * @param supabase Supabase 客戶端實例
 * @param table 資料表名
 * @param id 記錄ID
 * @param idField 主鍵欄位名
 * @returns 刪除結果和可能的錯誤
 */
export const removeRecord = async (
  supabase: SupabaseClient,
  table: TableName,
  id: string,
  idField: string = "unique_id"
): Promise<DeleteOperationResult> => {
  try {
    console.log(`Deleting record from ${table} with ${idField}=${id}`);

    const { error } = await supabase.from(table).delete().eq(idField, id);

    if (error) {
      throw error;
    }

    console.log(`Record deleted from ${table} with ${idField}=${id}`);

    return { error: null };
  } catch (err) {
    console.error(`Error deleting data from ${table}:`, err);
    const error = err instanceof Error ? err : new Error(String(err));
    return { error };
  }
};
