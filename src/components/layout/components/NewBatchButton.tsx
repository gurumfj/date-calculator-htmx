import React from "react";
import { useLocation, useNavigate } from "react-router-dom";

const NewBatchButton: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();

  if (location.pathname !== "/batches") return null;

  return (
    <button
      className="
        absolute right-4
        bg-blue-500 
        w-10 h-10 
        rounded-full 
        flex items-center justify-center 
        shadow-md 
        hover:bg-blue-600 
        transition-colors
      "
      onClick={() => navigate("/batch/new")}
      aria-label="新建批次"
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        className="h-6 w-6 text-white"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M12 6v6m0 0v6m0-6h6m-6 0H6"
        />
      </svg>
    </button>
  );
};

export default NewBatchButton;
