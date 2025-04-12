import React from "react";

// 導航項目類型
export interface NavItem {
  path: string;
  icon: React.ReactNode;
  label: string;
}

// 響應式側邊欄的Props類型
export interface ResponsiveSidebarProps {
  className?: string;
  isSidebarOpen?: boolean;
  onSidebarOpenChange?: (isOpen: boolean) => void;
}
