import React, { ReactNode } from "react";
import HamburgerButton from "./HamburgerButton";
import { useSidebar } from "../contexts/SidebarContext";

interface PageNavbarProps {
  title: string;
  leftActions?: ReactNode;
  rightActions?: ReactNode;
}

/**
 * 頁面頂部導航欄組件
 *
 * 可直接在頁面內使用，不需通過 context
 * 自動處理漢堡按鈕與側邊欄的交互
 */
const PageNavbar: React.FC<PageNavbarProps> = ({
  title,
  leftActions,
  rightActions,
}) => {
  // 使用側邊欄上下文來獲取側邊欄狀態
  const { isSidebarOpen, setIsSidebarOpen } = useSidebar();

  return (
    <nav className="fixed top-0 left-0 right-0 bg-white shadow-sm h-14 flex items-center px-4 border-b border-gray-200 z-40">
      {/* 左側區域 - 含漢堡按鈕和操作區 */}
      <div className="flex items-center h-full">
        {/* 漢堡按鈕容器 */}
        <div className="flex items-center justify-center w-10">
          <HamburgerButton
            isSidebarOpen={isSidebarOpen}
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
          />
        </div>

        {/* 左側操作區域 - 與漢堡按鈕保持適當間距 */}
        {leftActions && (
          <div className="ml-4 flex items-center">
            {leftActions}
          </div>
        )}
      </div>

      {/* 中間標題 - 使用絕對定位確保居中 */}
      <h1 className="absolute left-1/2 top-1/2 transform -translate-x-1/2 -translate-y-1/2 text-lg font-semibold text-gray-800 whitespace-nowrap overflow-hidden text-ellipsis max-w-[60%]">
        {title}
      </h1>

      {/* 右側區域 - 自動靠右對齊 */}
      <div className="ml-auto flex items-center h-full">
        {rightActions}
      </div>
    </nav>
  );
};

export default PageNavbar;
