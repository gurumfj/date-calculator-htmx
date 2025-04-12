import { createClient } from "@supabase/supabase-js";
import type { Database } from "@app-types";

/**
 * TODO: FEATURE - 在前端設定網頁自定義直連URL
 */

const getSupabaseUrl = () => {
  // Supabase 直連
  if (import.meta.env.VITE_SUPABASE_URL) {
    console.log("Supabase 直連", import.meta.env.VITE_SUPABASE_URL);
    return `${import.meta.env.VITE_SUPABASE_URL}`;
  }

  // 生產環境 Backend proxy
  const getCurrentProtocol = () => {
    return window.location.protocol === "https:" ? "https" : "http";
  };
  const getCurrentHost = () => {
    return window.location.host;
  };
  const getProxyPath = () => {
    return import.meta.env.VITE_SUPABASE_PATH || "/proxy";
  };
  console.log(
    "生產環境 Backend proxy",
    getCurrentProtocol(),
    getCurrentHost(),
    getProxyPath()
  );
  return `${getCurrentProtocol()}://${getCurrentHost()}${getProxyPath()}`;
};

const getSupabaseAnonKey = () => {
  return import.meta.env.VITE_SUPABASE_ANON_KEY || "dummy";
};

// 使用TypeScript定義創建具有類型的Supabase客戶端
const supabase = createClient<Database>(getSupabaseUrl(), getSupabaseAnonKey());

export default supabase;
