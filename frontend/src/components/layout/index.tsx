import React from "react";
import ResponsiveSidebar from "./ResponsiveSidebar";
import { SidebarProvider, useSidebar } from "./contexts/SidebarContext";

interface AppLayoutProps {
  children: React.ReactNode;
}

const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  return (
    <SidebarProvider>
      <AppLayoutContent>{children}</AppLayoutContent>
    </SidebarProvider>
  );
};

// 分離內部組件以使用 hooks
const AppLayoutContent: React.FC<AppLayoutProps> = ({ children }) => {
  const { isSidebarOpen, setIsSidebarOpen } = useSidebar();

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <div className="flex flex-1 overflow-hidden">
        {/* 使用響應式側邊欄 */}
        <ResponsiveSidebar
          isSidebarOpen={isSidebarOpen}
          onSidebarOpenChange={setIsSidebarOpen}
        />

        {/* 主內容 - 保留 pt-14 確保不被 navbar 遮擋 */}
        <main className="flex-1 overflow-auto relative pt-14 pb-16">
          {children}
        </main>
      </div>
    </div>
  );
};

export default AppLayout;
