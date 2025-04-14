import React from "react";
import { Link } from "react-router-dom";

interface SidebarLogoProps {
  isCollapsed: boolean;
}

const SidebarLogo: React.FC<SidebarLogoProps> = ({ isCollapsed }) => {
  return (
    <Link to="/" className="block">
      <h2
        className={`
          font-bold text-center
          ${isCollapsed ? "text-xl" : "text-2xl"}
          text-blue-600
        `}
      >
        {isCollapsed ? "CS" : "CleanSales"}
      </h2>
      <p
        className={`
          text-gray-500 text-xs text-center mt-1
          ${isCollapsed ? "hidden" : "block"}
        `}
      >
        智能養殖管理系統
      </p>
    </Link>
  );
};

export default SidebarLogo;
