import React, {
  useMemo,
  useCallback /**
   * 批次卡片元件
   * Why: 提供批次主列表的摘要資訊、互動入口與快速操作，提升批次管理效率與 UX。
   *      強調選取狀態、複製批次資訊等核心場景。
   */,
} from "react";
import {
  calculateBatchAgeRange,
  calculateTotalChickens,
  extractFeedManufacturers,
  calculateSalesPercentage,
  getBatchStateDisplay,
} from "@utils/batchCalculations";
import { calculateDayAge, calculateWeekAge } from "@utils/dateUtils";
import {
  FaCalendarDay,
  FaMars,
  FaVenus,
  FaTags,
  FaCopy,
  FaExchangeAlt,
  FaSpinner,
} from "react-icons/fa";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { BATCH_ACTIVITY_COLORS } from "@app-types";
import { useBatchStore } from "../store/useBatchStore";
import { useFetchBatchAggregates } from "../hooks/useFetchBatches";
import { useNavigate } from "react-router-dom";
import { useToast } from "@/hooks/use-toast";

// --- Main Card Component ---
interface BatchCardProps {
  batchName: string;
}

export const BatchCard: React.FC<BatchCardProps> = ({ batchName }) => {
  // 1. 先取得 store 中的狀態
  // 只讀取 selectedBatchName，不直接 set，避免副作用
  const { selectedBatchName } = useBatchStore();

  // 2. 從 API 獲取批次數據
  const {
    data: batchAggregate,
    isLoading,
    isError,
  } = useFetchBatchAggregates(batchName);

  // 3. 計算衍生狀態
  const isSelected = selectedBatchName === batchName;
  const navigate = useNavigate();

  //Toast
  const { toast } = useToast();

  // 4. 定義事件處理函數
  // 點擊卡片時僅透過 navigate 控制路由，store 狀態由 BatchPage useEffect 控制
  const handleCardClick = useCallback(() => {
    if (!batchAggregate) return;
    if (selectedBatchName === batchName) {
      // 已選取，再點擊回到列表（不帶 batchName）
      navigate(`/batches`);
    } else {
      // 切換到該批次
      navigate(`/batches/${batchName}`);
    }
  }, [batchAggregate, batchName, selectedBatchName, navigate]);

  const handleCopy = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      if (!batchAggregate) return;

      // 自定義批次文本格式
      const localDateStr = new Date()
        .toLocaleDateString("zh-TW", {
          year: "numeric",
          month: "2-digit",
          day: "2-digit",
        })
        .replace(/\//g, "-");

      const weekAgeText = batchAggregate.breeds
        .map((r) => {
          const dayAge = calculateDayAge(r.breed_date, new Date());
          const weekAge = calculateWeekAge(dayAge);
          return `[${weekAge.week}.${weekAge.day}]`;
        })
        .join(", ");

      // 直接從標準化的索引對象獲取批次名稱
      const actualBatchName = batchAggregate.index.batch_name || batchName;

      // 組合批次名稱和週齡
      const copyText = `${actualBatchName}\n${localDateStr} ${weekAgeText}`;

      navigator.clipboard.writeText(copyText);
      toast({
        title: "批次名稱已複製",
        description: copyText,
      });
    },
    [batchAggregate, batchName, toast]
  );

  // 5. 計算批次數據
  const batchData = useMemo(() => {
    // 始終提供默認值
    const defaultData = {
      maxWeekAge: { week: 0, day: 0 },
      minWeekAge: null,
      totalMale: 0,
      totalFemale: 0,
      feedManufacturers: "",
      salesPercentage: 0,
      batchActivity: "breeding" as const,
    };

    if (!batchAggregate) return defaultData;

    try {
      const { maxWeekAge, minWeekAge } = calculateBatchAgeRange(batchAggregate);
      const { totalMale, totalFemale } = calculateTotalChickens(batchAggregate);
      const feedManufacturers = extractFeedManufacturers(batchAggregate);
      const salesPercentage = calculateSalesPercentage(batchAggregate);
      // 現在 index 已經標準化為單一對象
      const batchActivity =
        batchAggregate.index.data?.batchActivity || "breeding";

      return {
        maxWeekAge,
        minWeekAge,
        totalMale,
        totalFemale,
        feedManufacturers,
        salesPercentage,
        batchActivity,
      };
    } catch (error) {
      console.error("計算批次數據時出錯:", error);
      return defaultData;
    }
  }, [batchAggregate]);

  // 6. 定義標題文本
  const titleText = isSelected ? "點擊返回銷售報表" : "點擊查看詳細資訊";

  // 7. 渲染加載狀態
  if (isLoading || isError || !batchAggregate) {
    return (
      <Card
        title={titleText}
        className="cursor-pointer transition-all duration-200 p-3"
      >
        <div className="flex items-center justify-center">
          <FaSpinner className="animate-spin text-[#007AFF] w-6 h-6" />
        </div>
      </Card>
    );
  }

  // 8. 提取計算的數據
  const {
    maxWeekAge,
    minWeekAge,
    totalMale,
    totalFemale,
    feedManufacturers,
    salesPercentage,
    batchActivity,
  } = batchData;

  // 9. 獲取顏色
  const activityColor = BATCH_ACTIVITY_COLORS[batchActivity];

  // 10. 渲染主要內容
  return (
    <Card
      title={titleText}
      className={cn(
        "cursor-pointer transition-all duration-200 p-3",
        // Why: 選取狀態高亮顯示，提升批次切換辨識度與操作手感
        isSelected
          ? "ring-2 ring-[#007AFF] border-transparent shadow-lg bg-blue-50 scale-[1.02] z-10"
          : "bg-white/90 hover:bg-white hover:shadow-md"
      )}
      // Why: 點擊卡片可切換批次，簡化批次切換流程
      onClick={handleCardClick}
    >
      {/* 標題、狀態和複製按鈕 */}
      {/* Why: 卡片頂部顯示批次名稱、狀態與複製操作，方便辨識與快速操作 */}
      <CardHeader className="flex-row justify-between items-center p-0 pb-2 space-y-0">
        {/* Why: 批次名稱為主識別資訊，選取時顯示切換圖示，強化 UX 回饋 */}
        <CardTitle className="text-base font-semibold truncate mr-2 text-[#1C1C1E]">
          {batchAggregate.index.batch_name}
          {isSelected && (
            <FaExchangeAlt className="inline-block ml-1 text-[#007AFF] w-3 h-3" />
          )}
        </CardTitle>
        {/* Why: 狀態徽章與複製按鈕並列，方便用戶一眼辨識批次狀態並快速複製資訊 */}
        <div className="flex items-center">
          {/* Why: 狀態色彩依據批次活動自動變化，提升狀態辨識度 */}
          <Badge
            style={{
              backgroundColor: activityColor.bg,
              color: "white",
            }}
            className="rounded-md text-xs font-medium mr-1"
          >
            {getBatchStateDisplay(batchActivity).label}
          </Badge>
          {/* Why: 一鍵複製批次名稱與週齡，方便用戶在多處重複使用批次資訊 */}
          <Button
            onClick={handleCopy}
            variant="ghost"
            size="icon"
            className="h-6 w-6 p-1 hover:bg-gray-100"
            aria-label="複製批次名稱和週齡"
            title="複製批次名稱和週齡"
          >
            <FaCopy className="text-[#8E8E93] w-3 h-3" />
          </Button>
        </div>
      </CardHeader>

      {/* Why: 主內容區顯示批次關鍵指標（週齡、飼料、雞隻數），讓用戶一眼掌握核心資訊 */}
      <CardContent className="p-0">
        {/* 資訊網格：週齡、飼料、雞隻 */}
        {/* Why: 以網格方式分區顯示週齡、飼料、雞隻等資訊，提升可讀性與響應式體驗 */}
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
              <span className="font-medium text-[#1C1C1E]">
                {totalFemale} 隻
              </span>
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
