import React from "react";
import { useNavigate } from "react-router-dom";
import PageNavbar from "@components/layout/components/PageNavbar";

const NotFoundPage: React.FC = () => {
  const navigate = useNavigate();
  return (
    <>
      {/* 頁面頂部導航欄 */}
      <PageNavbar title="找不到頁面" />

      <div className="min-h-screen flex items-center justify-center p-4 bg-gray-50">
        <div className="max-w-md w-full text-center">
          <h1 className="text-8xl font-bold text-gray-300">404</h1>
          <h2 className="text-2xl font-semibold text-gray-800 mt-4">
            頁面未找到
          </h2>
          <p className="text-gray-600 mt-2 mb-6">
            很抱歉，您請求的頁面不存在或已被移除。
          </p>
          <button
            onClick={() => navigate(-1)}
            className="inline-block bg-blue-500 hover:bg-blue-600 text-white font-medium py-2 px-6 rounded-lg transition-colors"
          >
            返回
          </button>
        </div>
      </div>
    </>
  );
};

export default NotFoundPage;
