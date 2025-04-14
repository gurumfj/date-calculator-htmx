import React from 'react';

interface EmptyStateProps {
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({ className = "" }) => {
  return (
    <div className={`bg-white/90 backdrop-blur-lg rounded-2xl shadow-lg shadow-blue-500/5 p-10 text-center transition-all duration-300 mx-4 mt-4 ${className}`}>
      <div>
        <svg
          className="w-16 h-16 mx-auto mb-4 text-[#8E8E93]"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
          />
        </svg>
      </div>
      <h3 className="text-xl font-semibold mb-2 text-[#1C1C1E]">
        沒有找到批次
      </h3>
      <p className="text-[#8E8E93]">
        請嘗試調整篩選條件或搜尋關鍵字
      </p>
    </div>
  );
};
