import React from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { BatchActivity, BatchActivityOptions } from "@/types";
import {
  useFetchBatchAggregates,
  useUpdateBatchCustomData,
} from "../BatchesPage/hooks";

interface BatchActivityEditProps {
  batchName: string;
}

const BatchActivityEdit: React.FC<BatchActivityEditProps> = ({ batchName }) => {
  const { data: batch, isLoading, error } = useFetchBatchAggregates(batchName);

  const { mutate, isPending: isUpdating } = useUpdateBatchCustomData(batchName);

  const handleActivityChange = (newActivity: BatchActivity) => {
    const newCustomData = { ...batch?.index?.data, batchActivity: newActivity };
    console.log(`Batch: ${batchName}, New Activity Selected: ${newActivity}`);
    mutate({ batchName, customData: newCustomData });
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

  return (
    <Select
      value={batch.index.data?.batchActivity || ""}
      onValueChange={(newValue) =>
        handleActivityChange(newValue as BatchActivity)
      }
      disabled={isUpdating}
    >
      <SelectTrigger className="w-[180px]">
        <SelectValue placeholder="選擇活動狀態" />
      </SelectTrigger>
      <SelectContent>
        {BatchActivityOptions.map((option) => (
          <SelectItem key={option.value} value={option.value}>
            {option.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
};

export default BatchActivityEdit;
