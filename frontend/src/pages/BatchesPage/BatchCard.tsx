import React from "react";
import { BatchAggregate } from "@app-types";
import {
  calculateBatchAgeRange,
  calculateTotalChickens,
  extractFeedManufacturers,
  determineBatchState,
  calculateSalesPercentage,
  generateBatchCopyText,
  getBatchStateDisplay,
} from "@utils/batchCalculations";
import {
  FaCalendarDay,
  FaMars,
  FaVenus,
  FaTags,
  FaCopy,
  FaExchangeAlt,
} from "react-icons/fa";

// --- Main Card Component ---
interface BatchCardProps {
  batch: BatchAggregate;
  isSelected: boolean;
  onClick: () => void;
}

export const BatchCard: React.FC<BatchCardProps> = ({
  batch,
  isSelected,
  onClick,
}) => {
  // --- 使用計算工具函數 ---
  const { maxWeekAge, minWeekAge } = calculateBatchAgeRange(batch);
  const { totalMale, totalFemale } = calculateTotalChickens(batch);
  const feedManufacturers = extractFeedManufacturers(batch);
  const batchState = determineBatchState(batch);
  const salesPercentage = calculateSalesPercentage(batch);
  const stateDisplay = getBatchStateDisplay(batchState);

  // --- 事件處理函數 ---
  const handleCopy = (e: React.MouseEvent) => {
    e.stopPropagation(); // 防止觸發卡片的 onClick
    const copyText = generateBatchCopyText(batch);

    navigator.clipboard
      .writeText(copyText)
      .then(() => {
        console.log("Copied to clipboard:", copyText);
        // 可以選擇性地添加用戶反饋（例如：toast通知）
      })
      .catch((err) => {
        console.error("Failed to copy text: ", err);
        // 可以選擇性地添加錯誤反饋
      });
  };

  // --- 渲染 ---
  return (
    <div
      key={batch.batchName}
      className={`p-3 rounded-lg cursor-pointer transition-all duration-200 border
                ${
                  isSelected
                    ? "bg-white ring-2 ring-[#007AFF] shadow-md border-transparent"
                    : "bg-white/90 hover:bg-white hover:shadow-md border-gray-200"
                }`}
      onClick={onClick}
      title={isSelected ? "點擊返回銷售報表" : "點擊查看詳細資訊"}
    >
      {/* 標題、狀態和複製按鈕 */}
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-base font-semibold text-[#1C1C1E] truncate mr-2">
          {batch.batchName}
          {isSelected && (
            <FaExchangeAlt className="inline-block ml-1 text-[#007AFF] w-3 h-3" />
          )}
        </h3>
        <div className="flex items-center">
          <span
            className={`px-2 py-0.5 rounded-md text-xs font-medium ${stateDisplay.bgClass} ${stateDisplay.textClass} whitespace-nowrap`}
          >
            {stateDisplay.label}
          </span>
          <button
            onClick={handleCopy}
            className="ml-1 p-1 hover:bg-gray-100 rounded-full transition-colors"
            title="複製批次名稱和週齡"
          >
            <FaCopy className="text-[#8E8E93] w-3 h-3" />
          </button>
        </div>
      </div>

      {/* 資訊網格：週齡、飼料、雞隻 */}
      <div className="grid grid-cols-2 gap-2 text-sm mb-2">
        <div className="flex items-center space-x-2">
          <FaCalendarDay className="text-[#8E8E93] w-3 h-3 flex-shrink-0" />
          <div className="truncate">
            <span className="text-[#8E8E93]">週齡: </span>
            <span className="font-medium text-[#1C1C1E]">
              {maxWeekAge.week}.{maxWeekAge.day}
              {minWeekAge && ` ~ ${minWeekAge.week}.${minWeekAge.day}`}
            </span>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <FaTags className="text-[#8E8E93] w-3 h-3 flex-shrink-0" />
          <div className="truncate">
            <span className="text-[#8E8E93]">飼料: </span>
            <span className="font-medium text-[#1C1C1E]">
              {feedManufacturers || "-"}
            </span>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <FaMars className="text-[#8E8E93] w-3 h-3 flex-shrink-0" />
          <div className="truncate">
            <span className="text-[#8E8E93]">公雞: </span>
            <span className="font-medium text-[#1C1C1E]">{totalMale} 隻</span>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <FaVenus className="text-[#8E8E93] w-3 h-3 flex-shrink-0" />
          <div className="truncate">
            <span className="text-[#8E8E93]">母雞: </span>
            <span className="font-medium text-[#1C1C1E]">{totalFemale} 隻</span>
          </div>
        </div>
      </div>

      {/* 銷售進度條 */}
      {salesPercentage > 0 && (
        <div className="mt-2">
          <div className="flex justify-between items-center mb-1 text-xs">
            <span className="font-medium text-[#8E8E93]">銷售進度</span>
            <span className="font-medium text-[#007AFF]">
              {(salesPercentage * 100).toFixed(1)}%
            </span>
          </div>
          <div className="h-1.5 bg-[#F2F2F7] rounded-full overflow-hidden">
            <div
              className="h-full bg-[#007AFF] rounded-full transition-all duration-300"
              style={{
                width: `${salesPercentage * 100}%`,
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
};
