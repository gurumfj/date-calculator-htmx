import { QueryClient } from "@tanstack/react-query";

// 創建一個客戶端實例，並設置默認選項
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // 重要的默認設置
      refetchOnWindowFocus: true, // 窗口聚焦時重新獲取
      refetchOnMount: true, // 組件掛載時重新獲取
      retry: 2, // 失敗時重試1次
      staleTime: 5 * 60 * 1000, // 數據5分鐘內被視為新鮮
      gcTime: 10 * 60 * 1000, // 未被使用的數據缓存10分鐘
    },
  },
});
