import React from "react";
import { Outlet } from "react-router-dom";
import { registerLocale } from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import { zhTW } from "date-fns/locale/zh-TW";

import { NotificationProvider } from "./contexts/NotificationContext";
import NotificationBar from "./components/common/NotificationBar";
import AppLayout from "./components/layout";
import { queryClient } from "./lib/react-query";
import { QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";

// 註冊中文區域設定
registerLocale("zh-TW", zhTW);

const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <NotificationProvider>
        <div className="flex flex-col h-screen bg-[#F2F2F7]">
          <NotificationBar />
          <div className="flex-1">
            <AppLayout>
              <Outlet />
            </AppLayout>
          </div>
        </div>
      </NotificationProvider>
      {/* 開發工具 (僅在開發環境顯示) */}
      {import.meta.env.DEV && (
        <ReactQueryDevtools initialIsOpen={false} position="bottom" />
      )}
    </QueryClientProvider>
  );
};

export default App;
