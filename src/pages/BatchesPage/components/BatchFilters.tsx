import React from "react";
import { ChickenBreedType, CHICKEN_BREEDS } from "@app-types";
import { useBatchStore } from "../store/useBatchStore";
import { addDays, subDays } from "date-fns";

// 引入 shadcn/ui 元件
import { Button } from "@/components/ui/button";
import { SortAsc, SortDesc, ChevronLeft, ChevronRight } from "lucide-react";

const DEFAULT_DATE_RANGE = {
  start: new Date(new Date().setDate(new Date().getDate() - 30)),
  end: new Date(),
};

/**
 * 批次篩選組件，負責批次列表的品種、日期、排序等條件選擇
 * Why: 將查詢條件與主內容分離，提升可維護性與擴充性
 */
export const BatchFilters: React.FC = () => {
  // 從 store 取得當前篩選條件與 setter，保持單一來源原則
  const { filter, setFilter, filterSettings } = useBatchStore();
  const { filterByBreed, sortOrder, filterByStart, filterByEnd } = filter;

  /**
   * 切換品種篩選條件
   * Why: 讓用戶能快速依品種分類查詢批次
   */
  const handleBreedChange = (breed: ChickenBreedType) => {
    setFilter({
      ...filter,
      filterByBreed: breed,
    });
  };

  /**
   * 日期區間往前移動（根據預設天數）
   * Why: 提供快速滑動查詢區間，提升 UX
   */
  const handlePrevDate = () => {
    setFilter({
      ...filter,
      filterByStart: filterByStart
        ? subDays(filterByStart, filterSettings.defaultDaysRange)
        : null,
      filterByEnd: filterByEnd
        ? subDays(filterByEnd, filterSettings.defaultDaysRange)
        : null,
    });
  };

  /**
   * 日期區間往後移動（根據預設天數）
   * Why: 提供快速滑動查詢區間，提升 UX
   */
  const handleNextDate = () => {
    setFilter({
      ...filter,
      filterByStart: filterByStart
        ? addDays(filterByStart, filterSettings.defaultDaysRange)
        : null,
      filterByEnd: filterByEnd
        ? addDays(filterByEnd, filterSettings.defaultDaysRange)
        : null,
    });
  };

  /**
   * 重設日期篩選條件到預設值
   * Why: 方便用戶一鍵回到預設查詢狀態
   */
  const handleResetDate = () => {
    setFilter({
      ...filter,
      filterByStart: DEFAULT_DATE_RANGE.start,
      filterByEnd: DEFAULT_DATE_RANGE.end,
    });
  };

  const toggleSortOrder = () => {
    setFilter({
      ...filter,
      sortOrder: filter.sortOrder === "asc" ? "desc" : "asc",
    });
  };

  return (
    <div className="flex items-center flex-wrap gap-2">
      <div className="flex flex-wrap items-center gap-1">
        {CHICKEN_BREEDS.map((breed) => (
          <Button
            key={breed}
            size="sm"
            variant={filterByBreed === breed ? "default" : "outline"}
            onClick={() => handleBreedChange(breed)}
            className="h-7 px-2 text-xs min-w-10"
          >
            {breed}
          </Button>
        ))}
      </div>

      {/* 日期區間操作按鈕群組，包含往前、往後、重設等操作 */}
      <div className="flex items-center gap-1">
        {/* 日期往前移動按鈕，方便用戶快速切換查詢區間 */}
        <Button
          variant="outline"
          size="sm"
          className="h-7 px-2 text-xs"
          onClick={handlePrevDate}
        >
          <ChevronLeft />
        </Button>

        {/* 顯示目前查詢區間，點擊可重設為預設範圍 */}
        <Button
          variant="outline"
          size="sm"
          className="h-7 px-2 text-xs"
          onClick={handleResetDate}
        >
          {filterByStart?.toLocaleDateString() +
            " - " +
            filterByEnd?.toLocaleDateString()}
        </Button>

        {/* 日期往後移動按鈕，方便用戶快速切換查詢區間 */}
        <Button
          variant="outline"
          size="sm"
          className="h-7 px-2 text-xs"
          onClick={handleNextDate}
        >
          <ChevronRight />
        </Button>
      </div>

      {/* 排序切換按鈕，支援升冪/降冪切換，強化 UX */}
      <Button
        variant="ghost"
        size="sm"
        onClick={toggleSortOrder}
        className="h-7 px-2 ml-auto"
      >
        {sortOrder === "asc" ? (
          <SortAsc className="w-4 h-4" />
        ) : (
          <SortDesc className="w-4 h-4" />
        )}
      </Button>
    </div>
  );
};
