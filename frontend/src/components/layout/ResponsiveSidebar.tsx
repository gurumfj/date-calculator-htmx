import React, { useState } from "react";
import { ResponsiveSidebarProps } from "./utils/types";
import HamburgerButton from "./components/HamburgerButton";
import NavbarTitle from "./components/NavbarTitle";
import NewBatchButton from "./components/NewBatchButton";
import SidebarLogo from "./components/SidebarLogo";
import SidebarNavItems from "./components/SidebarNavItems";
import SidebarCollapseButton from "./components/SidebarCollapseButton";

const ResponsiveSidebar: React.FC<ResponsiveSidebarProps> = ({
  className = "",
}) => {
  // 只保留必要的狀態
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);

  return (
    <>
      {/* 頂部導航欄 */}
      <nav
        className="
          fixed top-0 left-0 right-0 
          bg-white 
          shadow-sm 
          h-14 
          flex 
          items-center 
          px-4 
          border-b 
          border-gray-200 
          z-40
        "
      >
        {/* 漢堡按鈕 */}
        <HamburgerButton
          isSidebarOpen={isSidebarOpen}
          onClick={() => setIsSidebarOpen(true)}
        />

        {/* 路由標題 */}
        <NavbarTitle />

        {/* 新建批次按鈕 */}
        <NewBatchButton />
      </nav>

      {/* 遮罩層 */}
      <div
        className={`
          fixed inset-0 bg-black bg-opacity-50 z-40 transition-opacity duration-300
          ${isSidebarOpen ? "opacity-100" : "opacity-0 pointer-events-none"}
          md:hidden
        `}
        onClick={() => setIsSidebarOpen(false)}
      />

      {/* 側邊欄 */}
      <aside
        className={`
          fixed md:relative left-0 top-0 bottom-0 z-50
          ${isCollapsed ? "w-20" : "w-64"} 
          bg-white h-full transition-all duration-300 ease-in-out
          ${isSidebarOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"}
          shadow-md flex flex-col
          mt-14 md:mt-0
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
              if (window.innerWidth < 768) setIsSidebarOpen(false);
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
