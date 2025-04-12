import React, { useState, useCallback } from "react";
import { useSortedBatchAggregates } from "../../hooks/useSortedBatchAggregates";
import { BatchFilters } from "./BatchFilters";
import { BatchList } from "./BatchList";
import BatchDetailPanel from "./BatchDetailPanel";
import { useParams, useNavigate } from "react-router-dom";
import LoadingSpinner from "@components/common/LoadingSpinner";
import PageNavbar from "@components/layout/components/PageNavbar";
import NewBatchButton from "./components/NewBatchButton";
import BackButton from "@components/layout/components/BackButton";
type SortOrder = "asc" | "desc";

const BatchesPage: React.FC = () => {
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc");
  const navigate = useNavigate();

  // 返回列表
  const handleBackToList = useCallback(() => {
    navigate("/batches");
  }, [navigate]);

  const toggleSortOrder = () =>
    setSortOrder((prev) => (prev === "asc" ? "desc" : "asc"));

  const {
    sortedBatches,
    isLoading,
    error,
    count,
    selectedBreed,
    handleBreedChange,
    isCompleted,
    toggleIsCompleted,
  } = useSortedBatchAggregates(sortOrder);

  // 從URL獲取批次名稱
  const { batchName } = useParams();
  console.log("Batch Name from URL:", batchName);

  // 找到選中的批次
  const selectedBatch = batchName
    ? sortedBatches.find((b) => b.batchName === batchName) || null
    : null;

  // 準備導航欄內容
  const leftActions = selectedBatch ? (
    <BackButton
      onClick={handleBackToList}
      iconOnly={true} // 使用純圖標模式
      title="返回列表"
    />
  ) : null;
  const rightActions = <NewBatchButton isInNavbar={true} />;

  // 處理載入和錯誤狀態
  if (error)
    return (
      <div className="text-center p-4 text-red-500">
        載入錯誤：{error.message}
      </div>
    );

  return (
    <LoadingSpinner show={isLoading}>
      {/* 頁面頂部導航欄 */}
      <PageNavbar
        title={selectedBatch ? `批次: ${selectedBatch.batchName}` : "批次管理"}
        leftActions={leftActions}
        rightActions={rightActions}
      />

      <div className="container mx-auto p-4 lg:p-6">
        {/* 移動裝置返回按鈕已移至頂部導航欄 */}

        {/* 根據是否選中批次使用不同的布局 */}
        {selectedBatch ? (
          // 選中批次時的詳情視圖布局 (Flex)
          <div className="flex flex-col lg:flex-row lg:gap-6">
            {/* 左側：列表區域 - 在移動裝置隱藏，在桌面版顯示 */}
            <div className="hidden lg:block lg:w-1/3">
              <BatchFilters
                selectedBreed={selectedBreed}
                isCompleted={isCompleted}
                sortOrder={sortOrder}
                handleBreedChange={handleBreedChange}
                toggleIsCompleted={toggleIsCompleted}
                toggleSortOrder={toggleSortOrder}
              />

              <div className="mb-4">
                <p className="text-sm text-gray-600">總筆數: {count}</p>
              </div>

              <div
                className="lg:overflow-y-auto lg:custom-scrollbar"
                style={{ maxHeight: "calc(100vh - 220px)" }}
              >
                <BatchList batches={sortedBatches} isLoading={isLoading} />
              </div>
            </div>

            {/* 右側：詳情區域 */}
            <div
              className="w-full lg:w-2/3 lg:overflow-y-auto lg:custom-scrollbar"
              style={{ maxHeight: "calc(100vh - 120px)" }}
            >
              <div className="bg-white rounded-lg shadow-md p-6">
                <BatchDetailPanel batch={selectedBatch} />
              </div>
            </div>
          </div>
        ) : (
          // 未選中批次時的網格布局 (Grid)
          <div>
            {/* 過濾器部分 */}
            <div className="mb-6">
              <BatchFilters
                selectedBreed={selectedBreed}
                isCompleted={isCompleted}
                sortOrder={sortOrder}
                handleBreedChange={handleBreedChange}
                toggleIsCompleted={toggleIsCompleted}
                toggleSortOrder={toggleSortOrder}
              />

              <div className="mb-4">
                <p className="text-sm text-gray-600">總筆數: {count}</p>
              </div>
            </div>

            {/* 網格列表 - 響應式調整列數 */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              <div className="col-span-1 sm:col-span-2 lg:col-span-3 xl:col-span-4">
                <BatchList
                  batches={sortedBatches}
                  isLoading={isLoading}
                  gridView={true}
                />
              </div>
            </div>
          </div>
        )}
      </div>
    </LoadingSpinner>
  );
};

export default BatchesPage;
