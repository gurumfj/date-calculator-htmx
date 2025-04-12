import React from "react";
import { FaChevronLeft, FaChevronRight } from "react-icons/fa";

interface SidebarCollapseButtonProps {
  isCollapsed: boolean;
  onClick: () => void;
}

const SidebarCollapseButton: React.FC<SidebarCollapseButtonProps> = ({
  isCollapsed,
  onClick
}) => {
  return (
    <div className="p-4 border-t border-gray-200 hidden md:block">
      <button
        onClick={onClick}
        className="w-full flex items-center justify-center py-2 px-4 rounded-lg bg-gray-100 text-gray-600 hover:bg-gray-200"
        aria-label={isCollapsed ? "展開側邊欄" : "收合側邊欄"}
      >
        {isCollapsed ? (
          <FaChevronRight className="h-4 w-4" />
        ) : (
          <>
            <FaChevronLeft className="h-4 w-4 mr-2" />
            <span className="text-sm">收合側邊欄</span>
          </>
        )}
      </button>
    </div>
  );
};

export default SidebarCollapseButton;
