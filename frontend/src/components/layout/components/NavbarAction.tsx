import React, { ReactNode } from "react";

interface NavbarActionProps {
  onClick?: () => void;
  icon?: ReactNode;
  label?: string;
  children?: ReactNode;
  className?: string;
  iconPosition?: "left" | "right";
  iconOnly?: boolean;
  title?: string; // 提示文字，用於 hover 顯示
}

/**
 * NavbarAction 組件 - 為導航欄操作提供統一的樣式
 * 支持純圖標按鈕、帶標籤的按鈕或自定義內容
 *
 * 使用方式：
 * 1. 純圖標：<NavbarAction icon={<HomeIcon />} iconOnly title="首頁" />
 * 2. 圖標+文字：<NavbarAction icon={<HomeIcon />} label="首頁" />
 * 3. 自定義內容：<NavbarAction>自定義內容</NavbarAction>
 */
const NavbarAction: React.FC<NavbarActionProps> = ({
  onClick,
  icon,
  label,
  children,
  className = "",
  iconPosition = "left",
  iconOnly = false,
  title,
}) => {
  // 如果提供了 children，直接渲染它們但應用預設樣式
  if (children) {
    return (
      <div
        onClick={onClick}
        className={`flex items-center h-10 px-3 rounded-md hover:bg-gray-100 transition-colors cursor-pointer ${className}`}
        title={title}
      >
        {children}
      </div>
    );
  }

  // 純圖標模式
  if (iconOnly && icon) {
    return (
      <div
        onClick={onClick}
        className={`flex items-center justify-center w-10 h-10 rounded-md hover:bg-gray-100 transition-colors cursor-pointer ${className}`}
        title={title || label} // 如果沒有提供 title，則使用 label 作為提示
      >
        {icon}
      </div>
    );
  }

  // 標準模式：圖標加標籤
  return (
    <div
      onClick={onClick}
      className={`flex items-center h-10 px-3 rounded-md hover:bg-gray-100 transition-colors cursor-pointer ${className}`}
      title={title}
    >
      {icon && iconPosition === "left" && <div className="mr-2">{icon}</div>}
      {label && <span className="text-gray-700">{label}</span>}
      {icon && iconPosition === "right" && <div className="ml-2">{icon}</div>}
    </div>
  );
};

export default NavbarAction;
