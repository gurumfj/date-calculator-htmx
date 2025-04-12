import React from "react";
import { BatchAggregate } from "@app-types";
import { BatchCard } from "./BatchCard";
import { useLocation, useNavigate } from "react-router-dom";

interface BatchListProps {
  batches: (BatchAggregate & { latestDate?: number })[];
  isLoading: boolean;
  gridView?: boolean; // 添加網格視圖選項
}

export const BatchList: React.FC<BatchListProps> = ({
  batches,
  isLoading,
  gridView = false, // 預設為列表視圖
}) => {
  const location = useLocation();
  const navigate = useNavigate();

  // 從 URL 中解析出當前選中的 batchName
  const selectedBatchName = location.pathname.startsWith("/batches/")
    ? decodeURIComponent(location.pathname.split("/").pop() || "")
    : null;

  console.log("Selected Batch Name:", selectedBatchName);

  const handleCardClick = (batchName: string) => {
    if (batchName === selectedBatchName) {
      navigate("/batches");
      return;
    }
    // 轉址到 /batches/:batchName
    navigate(`/batches/${encodeURIComponent(batchName)}`);
  };

  // 顯示載入狀態
  if (isLoading) return <div className="py-6 text-center text-gray-500">載入中...</div>;

  // 顯示無資料狀態
  if (batches.length === 0) {
    return <div className="py-12 text-center text-gray-500">暫無資料</div>;
  }

  // 使用網格視圖
  if (gridView) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {batches.map((batch) => (
          <BatchCard
            key={batch.batchName}
            batch={batch}
            isSelected={batch.batchName === selectedBatchName}
            onClick={() => handleCardClick(batch.batchName)}
          />
        ))}
      </div>
    );
  }

  // 原列表視圖
  return (
    <div className="space-y-6">
      {batches.map((batch) => (
        <BatchCard
          key={batch.batchName}
          batch={batch}
          isSelected={batch.batchName === selectedBatchName}
          onClick={() => handleCardClick(batch.batchName)}
        />
      ))}
    </div>
  );
};
