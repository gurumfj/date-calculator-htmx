import React, { useState, useEffect } from "react";
import { ResponsiveSidebarProps } from "./utils/types";
import SidebarLogo from "./components/SidebarLogo";
import SidebarNavItems from "./components/SidebarNavItems";
import SidebarCollapseButton from "./components/SidebarCollapseButton";

const ResponsiveSidebar: React.FC<ResponsiveSidebarProps> = ({
  className = "",
  isSidebarOpen = false,
  onSidebarOpenChange,
}) => {
  // 側邊欄折疊狀態
  const [isCollapsed, setIsCollapsed] = useState(false);

  // 內部狀態，用於當沒有提供外部控制時
  const [internalIsSidebarOpen, setInternalIsSidebarOpen] = useState(false);

  // 使用提供的 onSidebarOpenChange 或者內部狀態
  const handleSidebarToggle = (isOpen: boolean) => {
    if (onSidebarOpenChange) {
      onSidebarOpenChange(isOpen);
    } else {
      setInternalIsSidebarOpen(isOpen);
    }
  };

  // 當 isSidebarOpen prop 變化時更新內部狀態（單向數據流）
  useEffect(() => {
    if (onSidebarOpenChange) {
      // 如果有外部控制，不需要更新內部狀態
    } else {
      // 否則，自行管理狀態
      setInternalIsSidebarOpen(isSidebarOpen);
    }
  }, [isSidebarOpen, onSidebarOpenChange]);

  // 確定實際使用的狀態
  const sidebarOpen = onSidebarOpenChange ? isSidebarOpen : internalIsSidebarOpen;

  return (
    <>
      {/* 遮罩層 */}
      <div
        className={`
          fixed inset-0 bg-black bg-opacity-50 z-40 transition-opacity duration-300
          ${sidebarOpen ? "opacity-100" : "opacity-0 pointer-events-none"}
          md:hidden
        `}
        onClick={() => handleSidebarToggle(false)}
      />

      {/* 側邊欄 */}
      <aside
        className={`
          fixed md:relative left-0 top-0 bottom-0 z-50
          ${isCollapsed ? "w-20" : "w-64"}
          bg-white h-full transition-all duration-300 ease-in-out
          ${sidebarOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"}
          shadow-md flex flex-col
          ${className}
        `}
      >
        {/* 頂部 Logo */}
        <div className="pt-5 pb-6 px-4 border-b border-gray-200 relative">
          <SidebarLogo isCollapsed={isCollapsed} />
        </div>

        {/* 導航項目 */}
        <nav className="p-4 mt-2 flex-1 overflow-y-auto">
          <SidebarNavItems
            isCollapsed={isCollapsed}
            onItemClick={() => {
              if (window.innerWidth < 768) handleSidebarToggle(false);
            }}
          />
        </nav>

        {/* 側邊欄收合按鈕 */}
        <SidebarCollapseButton
          isCollapsed={isCollapsed}
          onClick={() => setIsCollapsed(!isCollapsed)}
        />
      </aside>
    </>
  );
};

export default ResponsiveSidebar;
