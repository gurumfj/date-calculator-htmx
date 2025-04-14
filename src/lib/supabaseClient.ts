import { createClient } from "@supabase/supabase-js";
import type { Database } from "@app-types";
import { API_URL } from "./apiClient";
/**
 * TODO: FEATURE - 在前端設定網頁自定義直連URL
 */

const getSupabaseAnonKey = () => {
  return import.meta.env.VITE_SUPABASE_ANON_KEY || "dummy";
};

// 使用TypeScript定義創建具有類型的Supabase客戶端
const supabase = createClient<Database>(
  `${API_URL.origin}/proxy`,
  getSupabaseAnonKey()
);

export default supabase;
