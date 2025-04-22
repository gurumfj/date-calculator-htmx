import React from "react";
import { Outlet } from "react-router-dom";
import { registerLocale } from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import { zhTW } from "date-fns/locale/zh-TW";

import AppLayout from "./components/layout";
import { queryClient } from "./lib/react-query";
import { QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { Toaster } from "./components/ui/toaster";

// 註冊中文區域設定
registerLocale("zh-TW", zhTW);

const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="flex flex-col h-screen bg-[#F2F2F7]">
        <div className="flex-1">
          <AppLayout>
            <Outlet />
            <Toaster />
          </AppLayout>
        </div>
      </div>
      {/* 開發工具 (僅在開發環境顯示) */}
      {import.meta.env.DEV && (
        <ReactQueryDevtools initialIsOpen={false} position="bottom" />
      )}
    </QueryClientProvider>
  );
};

export default App;
