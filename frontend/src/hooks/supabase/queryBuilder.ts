import { SupabaseClient } from "@supabase/supabase-js";
import { TableName, QueryOptions } from "./types";

/**
 * 構建 Supabase 查詢
 * @param supabase Supabase 客戶端實例
 * @param table 要查詢的資料表名
 * @param options 查詢選項，包括過濾、排序、分頁等
 * @returns 構建的查詢物件
 */
export const buildQuery = (
  supabase: SupabaseClient,
  table: TableName,
  options: QueryOptions = {}
) => {
  let query = supabase.from(String(table)).select("*", { count: "exact" });

  // 應用等於過濾
  if (options.eq) {
    Object.entries(options.eq).forEach(([key, value]) => {
      query = query.eq(key, value);
    });
  }

  // 應用不等於過濾
  if (options.neq) {
    Object.entries(options.neq).forEach(([key, value]) => {
      query = query.neq(key, value);
    });
  }

  // 應用 in 过滤
  if (options.in) {
    Object.entries(options.in).forEach(([key, values]) => {
      query = query.in(key, values);
    });
  }

  // 應用大於過濾
  if (options.gt) {
    Object.entries(options.gt).forEach(([key, value]) => {
      query = query.gt(key, value);
    });
  }

  // 應用小於過濾
  if (options.lt) {
    Object.entries(options.lt).forEach(([key, value]) => {
      query = query.lt(key, value);
    });
  }

  // 應用大於等於過濾
  if (options.gte) {
    Object.entries(options.gte).forEach(([key, value]) => {
      query = query.gte(key, value);
    });
  }

  // 應用小於等於過濾
  if (options.lte) {
    Object.entries(options.lte).forEach(([key, value]) => {
      query = query.lte(key, value);
    });
  }

  // 應用模糊匹配過濾（區分大小寫）
  if (options.like) {
    Object.entries(options.like).forEach(([key, value]) => {
      query = query.like(key, value);
    });
  }

  // 應用模糊匹配過濾（不區分大小寫）
  if (options.ilike) {
    Object.entries(options.ilike).forEach(([key, value]) => {
      query = query.ilike(key, value);
    });
  }

  // 應用排序
  if (options.order) {
    query = query.order(options.order.column, {
      ascending: options.order.ascending !== false,
    });
  }

  // 應用分頁
  if (options.limit !== undefined) {
    query = query.limit(options.limit);
  }

  if (options.offset !== undefined) {
    query = query.range(
      options.offset,
      options.offset + (options.limit || 10) - 1
    );
  }

  return query;
};

/**
 * 比較查詢選項是否發生變化
 * @param currentOptions 當前查詢選項
 * @param lastOptionsString 上一次查詢選項的字符串表示
 * @returns 是否發生變化
 */
export const hasOptionsChanged = (
  currentOptions: QueryOptions,
  lastOptionsString: string
): [boolean, string] => {
  const currentOptionsString = JSON.stringify(currentOptions);
  return [currentOptionsString !== lastOptionsString, currentOptionsString];
};
