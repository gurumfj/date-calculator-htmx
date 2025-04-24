import React, { useState } from "react";
import { cn } from "@/lib/utils";
import { format } from "date-fns";
import { Calendar as CalendarIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  useFetchBatchAggregates,
  useUpdateBatchIndexFinalDate,
} from "@/hooks/useFetchBatches";

interface BatchFinalDateEditProps {
  batchName: string;
}

const BatchFinalDateEdit: React.FC<BatchFinalDateEditProps> = ({
  batchName,
}) => {
  const {
    data: batches,
    isLoading,
    error,
  } = useFetchBatchAggregates([batchName]);
  const batch = batches?.[0];

  const { mutate, isPending: isUpdating } =
    useUpdateBatchIndexFinalDate(batchName);

  // Popover 開關狀態
  const [isCalendarOpen, setIsCalendarOpen] = useState(false);

  const handleFinalDateChange = (newFinalDate: string) => {
    console.log(
      `Batch: ${batchName}, New Final Date Selected: ${newFinalDate}`
    );
    mutate({ batchName, finalDate: newFinalDate });
    setIsCalendarOpen(false); // 選擇後關閉日曆
  };

  if (error) {
    return <p>{error?.message}</p>;
  }

  if (!batch || isLoading) {
    return <p>載入中...</p>;
  }

  if (isUpdating) {
    return <p>更新中...</p>;
  }

  // 將 final_date 字串轉換為 Date 物件，如果不存在或格式錯誤則為 null
  const currentDate = batch?.index?.final_date
    ? new Date(batch.index.final_date)
    : null;

  return (
    <Popover open={isCalendarOpen} onOpenChange={setIsCalendarOpen}>
      <PopoverTrigger asChild>
        <Button
          variant={"outline"}
          className={cn(
            "w-[180px] justify-start text-left font-normal",
            !currentDate && "text-muted-foreground"
          )}
          disabled={isUpdating}
        >
          <CalendarIcon className="mr-2 h-4 w-4" />
          {currentDate ? (
            format(currentDate, "yyyy-MM-dd")
          ) : (
            <span>選擇日期</span>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-auto p-0">
        <Calendar
          mode="single"
          selected={currentDate ?? undefined} // selected 需要 Date 或 undefined
          onSelect={(date) => {
            if (date) {
              handleFinalDateChange(format(date, "yyyy-MM-dd"));
            }
          }}
          disabled={isUpdating}
          initialFocus
        />
      </PopoverContent>
    </Popover>
  );
};

export default BatchFinalDateEdit;
