import React from "react";
import { Link, useLocation } from "react-router-dom";
import {
  FaHome,
  FaList,
  FaChartBar,
  FaFlask,
  FaDatabase,
  FaWrench
} from "react-icons/fa";
import { NavItem } from "../utils/types";
import { isActive } from "../utils/helpers";

interface SidebarNavItemsProps {
  isCollapsed: boolean;
  onItemClick: () => void;
}

const SidebarNavItems: React.FC<SidebarNavItemsProps> = ({
  isCollapsed,
  onItemClick
}) => {
  const location = useLocation();

  // 導航項目列表
  const navItems: NavItem[] = [
    { path: "/", icon: <FaHome className="h-5 w-5" />, label: "首頁" },
    { path: "/batches", icon: <FaList className="h-5 w-5" />, label: "批次" },
    {
      path: "/reports",
      icon: <FaChartBar className="h-5 w-5" />,
      label: "報表",
    },
    {
      path: "/testing",
      icon: <FaFlask className="h-5 w-5" />,
      label: "測試"
    },
    {
      path: "/supabase-test",
      icon: <FaDatabase className="h-5 w-5" />,
      label: "Supabase",
    },
    {
      path: "/settings",
      icon: <FaWrench className="h-5 w-5" />,
      label: "設定",
    },
  ];

  return (
    <ul className="space-y-2">
      {navItems.map((item) => (
        <li key={item.path}>
          <Link
            to={item.path}
            onClick={() => {
              if (window.innerWidth < 768) onItemClick();
            }}
            className={`
              flex items-center px-4 py-3 rounded-lg transition-colors
              ${
                isActive(location.pathname, item.path)
                  ? "bg-blue-50 text-blue-700"
                  : "text-gray-700 hover:bg-gray-100"
              }
            `}
          >
            <span className="flex-shrink-0">{item.icon}</span>

            {/* 當不摺疊時顯示文字 */}
            {!isCollapsed && (
              <span className="ml-3 font-medium">{item.label}</span>
            )}
          </Link>
        </li>
      ))}
    </ul>
  );
};

export default SidebarNavItems;
