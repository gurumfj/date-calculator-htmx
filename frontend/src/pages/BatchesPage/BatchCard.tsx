import React from "react";
import {
  calculateBatchAgeRange,
  calculateTotalChickens,
  extractFeedManufacturers,
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
  FaSpinner,
} from "react-icons/fa";
import { useBatchAggregate } from "@/hooks/useBatchAggregateQueries";
import { 
  Card, 
  CardHeader, 
  CardTitle, 
  CardContent 
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { BATCH_ACTIVITY_COLORS } from "@app-types";

// --- Main Card Component ---
interface BatchCardProps {
  batchName: string;
  isSelected?: boolean;
  onClick?: (batchName: string) => void;
}

export const BatchCard: React.FC<BatchCardProps> = ({
  batchName,
  isSelected,
  onClick,
}) => {
  // 使用 Hook 獲取批次數據
  const batchAggregate = useBatchAggregate(batchName);

  // 如果還沒有獲取到完整資料，顯示載入狀態
  if (!batchAggregate) {
    return (
      <Card 
        className={cn(
          "cursor-pointer transition-all duration-200 p-3",
          isSelected ? "ring-2 ring-[#007AFF] border-transparent shadow-md" : "hover:shadow-md"
        )}
        onClick={() => onClick?.(batchName)}
      >
        <CardHeader className="p-0 mb-2 space-y-0">
          <CardTitle className="text-base font-semibold truncate">
            {batchName}
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0 flex items-center justify-center py-4">
          <FaSpinner className="animate-spin text-[#007AFF] w-5 h-5" />
          <span className="ml-2 text-sm text-gray-500">載入中...</span>
        </CardContent>
      </Card>
    );
  }

  // --- 使用計算工具函數 ---
  const { maxWeekAge, minWeekAge } = calculateBatchAgeRange(batchAggregate);
  const { totalMale, totalFemale } = calculateTotalChickens(batchAggregate);
  const feedManufacturers = extractFeedManufacturers(batchAggregate);
  const salesPercentage = calculateSalesPercentage(batchAggregate);
  const stateDisplay = getBatchStateDisplay(
    batchAggregate.customData.batchActivity
  );

  // --- 事件處理函數 ---
  const handleCopy = (e: React.MouseEvent) => {
    e.stopPropagation(); // 防止觸發卡片的 onClick
    const copyText = generateBatchCopyText(batchAggregate);

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
    <Card
      key={batchAggregate.batchIndex.batch_name}
      className={cn(
        "cursor-pointer transition-all duration-200 p-3",
        isSelected 
          ? "ring-2 ring-[#007AFF] border-transparent shadow-md" 
          : "bg-white/90 hover:bg-white hover:shadow-md"
      )}
      onClick={() => onClick?.(batchName)}
      title={isSelected ? "點擊返回銷售報表" : "點擊查看詳細資訊"}
    >
      {/* 標題、狀態和複製按鈕 */}
      <CardHeader className="flex-row justify-between items-center p-0 pb-2 space-y-0">
        <CardTitle className="text-base font-semibold truncate mr-2 text-[#1C1C1E]">
          {batchAggregate.batchIndex.batch_name}
          {isSelected && (
            <FaExchangeAlt className="inline-block ml-1 text-[#007AFF] w-3 h-3" />
          )}
        </CardTitle>
        <div className="flex items-center">
          <Badge 
            style={{ 
              backgroundColor: BATCH_ACTIVITY_COLORS[batchAggregate.customData.batchActivity].bg,
              color: "white" 
            }}
            className="rounded-md text-xs font-medium mr-1"
          >
            {stateDisplay.label}
          </Badge>
          <Button 
            onClick={handleCopy} 
            variant="ghost" 
            size="icon" 
            className="h-6 w-6 p-1 hover:bg-gray-100"
            title="複製批次名稱和週齡"
          >
            <FaCopy className="text-[#8E8E93] w-3 h-3" />
          </Button>
        </div>
      </CardHeader>

      <CardContent className="p-0">
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
      </CardContent>
    </Card>
  );
};