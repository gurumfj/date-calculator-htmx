import React from "react";
import { ChickenBreedType, CHICKEN_BREEDS } from "@app-types";
import { useBatchStore } from "@/stores/batchStore";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";

// 引入 shadcn/ui 元件
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { SortAsc, SortDesc, CheckCircle, XCircle, Filter, Calendar } from "lucide-react";

interface BatchFiltersProps {
  handleBreedChange: (breed: ChickenBreedType) => void;
  toggleIsCompleted: () => void;
  toggleSortOrder: () => void;
  totalCount?: number;
  handleDateChange?: (start: Date | null, end: Date | null) => void;
  compact?: boolean; // 是否使用精簡模式
}

export const BatchFilters: React.FC<BatchFiltersProps> = ({
  handleBreedChange,
  toggleIsCompleted,
  toggleSortOrder,
  totalCount,
  handleDateChange,
  compact = true, // 預設為精簡模式
}) => {
  const { queryParams } = useBatchStore();
  const { chickenBreed, isCompleted, sortOrder, start, end } = queryParams;

  // 精簡模式：使用水平布局，將所有元素都放在一行
  if (compact) {
    return (
      <div className="flex items-center flex-wrap gap-2">
        {/* 雞種選擇按鈕群組 */}
        <div className="flex flex-wrap items-center gap-1">
          {CHICKEN_BREEDS.map((breed) => (
            <Button
              key={breed}
              size="sm"
              variant={chickenBreed === breed ? "default" : "outline"}
              onClick={() => handleBreedChange(breed)}
              className="h-7 px-2 text-xs min-w-10"
            >
              {breed}
            </Button>
          ))}
        </div>
        
        {/* 排序按鈕 */}
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
        
        {/* 總筆數標籤 */}
        {totalCount !== undefined && (
          <Badge variant="outline" className="text-xs">
            {totalCount}
          </Badge>
        )}
      </div>
    );
  }
  
  // 完整模式：使用原來的垂直布局
  return (
    <div className="space-y-4 full-filter">
      {/* 品種篩選區 */}
      <div className="space-y-2">
        <div className="flex items-center">
          <Filter className="w-4 h-4 mr-2 text-muted-foreground" />
          <Label className="text-sm font-medium">雞種篩選</Label>
        </div>
        <div className="flex flex-wrap gap-2">
          {CHICKEN_BREEDS.map((breed) => (
            <Button
              key={breed}
              size="sm"
              variant={chickenBreed === breed ? "default" : "outline"}
              onClick={() => handleBreedChange(breed)}
              className="min-w-16"
            >
              {breed}
            </Button>
          ))}
        </div>
      </div>

      {/* 排序選項 */}
      <div className="flex items-center justify-between">
        <Label className="text-sm font-medium">排序方式</Label>
        <Button
          variant="outline"
          size="sm"
          onClick={toggleSortOrder}
          className="gap-2"
        >
          {sortOrder === "asc" ? (
            <>
              <SortAsc className="w-4 h-4" />
              日期舊到新
            </>
          ) : (
            <>
              <SortDesc className="w-4 h-4" />
              日期新到舊
            </>
          )}
        </Button>
      </div>

      <Separator className="my-3" />

      {/* 日期範圍選擇 */}
      {handleDateChange && (
        <div className="space-y-2">
          <div className="flex items-center">
            <Calendar className="w-4 h-4 mr-2 text-muted-foreground" />
            <Label className="text-sm font-medium">日期範圍</Label>
          </div>
          
          <div className="grid grid-cols-2 gap-2">
            <div className="space-y-1">
              <Label className="text-xs text-muted-foreground">開始日期</Label>
              <DatePicker
                selected={start || null}
                onChange={(date) => handleDateChange?.(date, end || null)}
                selectsStart
                startDate={start || null}
                endDate={end || null}
                locale="zh-TW"
                dateFormat="yyyy/MM/dd"
                placeholderText="選擇開始日期"
                className="w-full rounded-md border border-input p-2 text-sm"
                isClearable
              />
            </div>
            
            <div className="space-y-1">
              <Label className="text-xs text-muted-foreground">結束日期</Label>
              <DatePicker
                selected={end || null}
                onChange={(date) => handleDateChange?.(start || null, date)}
                selectsEnd
                startDate={start || null}
                endDate={end || null}
                minDate={start}
                locale="zh-TW"
                dateFormat="yyyy/MM/dd"
                placeholderText="選擇結束日期"
                className="w-full rounded-md border border-input p-2 text-sm"
                isClearable
              />
            </div>
          </div>
        </div>
      )}

      <Separator className="my-3" />

      {/* 完成狀態切換 */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Label className="text-sm font-medium">顯示已完成批次</Label>
          {isCompleted ? (
            <CheckCircle className="w-4 h-4 text-green-500" /> 
          ) : (
            <XCircle className="w-4 h-4 text-gray-400" />
          )}
        </div>
        <Switch
          checked={isCompleted}
          onCheckedChange={toggleIsCompleted}
        />
      </div>
      
      {/* 顯示總筆數 */}
      <div className="flex items-center mt-4">
        <Badge variant="outline" className="text-xs">
          總筆數: {totalCount}
        </Badge>
      </div>
    </div>
  );
};
