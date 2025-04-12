import React from "react";
import { FaBars } from "react-icons/fa";

interface HamburgerButtonProps {
  isSidebarOpen: boolean;
  onClick: () => void;
}

const HamburgerButton: React.FC<HamburgerButtonProps> = ({
  isSidebarOpen,
  onClick
}) => {
  return (
    <button
      onClick={onClick}
      className={`
        absolute left-4 p-2 rounded-md
        text-gray-700 hover:bg-gray-100 transition-opacity duration-300
        ${isSidebarOpen ? "opacity-0 pointer-events-none" : "opacity-100 pointer-events-auto"}
        md:hidden
      `}
      aria-label="開啟側邊欄"
    >
      <FaBars className="h-5 w-5" />
    </button>
  );
};

export default HamburgerButton;
