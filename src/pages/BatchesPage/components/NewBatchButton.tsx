import React from "react";
import { useLocation, useNavigate } from "react-router-dom";
import NavbarAction from "../../../components/layout/components/NavbarAction";
import { PlusIcon } from "@heroicons/react/24/outline";

interface NewBatchButtonProps {
  isInNavbar?: boolean;
  className?: string;
}

const NewBatchButton: React.FC<NewBatchButtonProps> = ({ 
  isInNavbar = true,
  className = "" 
}) => {
  const location = useLocation();
  const navigate = useNavigate();
  
  // 只在批次頁面顯示，除非明確指定顯示
  const shouldShow = location.pathname === "/batches" || isInNavbar === false;
  
  if (!shouldShow) return null;

  // 根據是否在導航欄中顯示不同樣式
  if (isInNavbar) {
    return (
      <NavbarAction
        onClick={() => navigate("/batch/new")}
        icon={<PlusIcon className="h-5 w-5" />}
        iconOnly={true}
        title="新建批次"
        className={`bg-blue-500 hover:bg-blue-600 text-white rounded-full ${className}`}
      />
    );
  }
  
  // 頁面內按鈕樣式
  return (
    <button
      className={`
        absolute right-4
        bg-blue-500 
        w-10 h-10 
        rounded-full 
        flex items-center justify-center 
        shadow-md 
        hover:bg-blue-600 
        transition-colors
        text-white
        ${className}
      `}
      onClick={() => navigate("/batch/new")}
      aria-label="新建批次"
      title="新建批次"
    >
      <PlusIcon className="h-6 w-6" />
    </button>
  );
};

export default NewBatchButton;