import React, { useCallback, useEffect, useState } from "react";
import { BatchFilters } from "./BatchFilters";
import BatchDetailPanel from "./BatchDetailPanel";
import { useParams, useNavigate } from "react-router-dom";
import LoadingSpinner from "@components/common/LoadingSpinner";
import PageNavbar from "@components/layout/components/PageNavbar";
import BackButton from "@components/layout/components/BackButton";
import { useBatchStore } from "@stores/batchStore";
import { ChickenBreedType, BatchActivity, CustomData } from "@app-types";
import {
  useBatchAggregate,
  useBatchAggregatesIndex,
  useUpdateBatchCustomData,
} from "@/hooks/useBatchAggregateQueries";
import { BatchCard } from "./BatchCard";

// 引入 shadcn/ui 元件
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { SlidersHorizontal, Filter, Loader2, Settings } from "lucide-react";
import { isEqual } from "date-fns";

const BatchesPage: React.FC = () => {
  // 過濾器顯示模式狀態
  const [showFullFilter, setShowFullFilter] = useState(false);

  // 切換過濾器顯示模式
  const toggleFilterMode = useCallback(() => {
    setShowFullFilter((prev) => !prev);
  }, []);
  // 使用 Zustand store 管理狀態
  const {
    queryParams,
    batchIndices,
    selectedBatchName,
    setQueryParams,
    setSelectedBatchName,
    setBatchIndices,
  } = useBatchStore();

  const { batchName } = useParams();
  // console.log(batchName);
  const navigate = useNavigate();

  // 使用 hook 獲取選中批次的詳細數據
  const selectedBatchAggregate = useBatchAggregate(batchName || null);
  // 設置更新批次活動的 mutation
  const updateBatchCustomData = useUpdateBatchCustomData();

  // 批次活動更新處理函數
  const handleUpdateBatchActivity = useCallback(
    (
      batchName: string,
      currentCustomData: CustomData,
      newActivity: BatchActivity
    ) => {
      if (!batchName) return;
      if (isEqual(currentCustomData.batchActivity, newActivity)) return;

      // 創建新的 customData 對象
      const newCustomData = {
        ...currentCustomData,
        batchActivity: newActivity,
      };

      // 更新批次活動
      updateBatchCustomData.mutate({
        batchName: batchName,
        customData: newCustomData,
      });

      // 刷新頁面
      // TODO: 用狀態管理來代替
      window.location.reload();
    },
    [updateBatchCustomData]
  );
  useEffect(() => {
    if (batchName) {
      setSelectedBatchName(batchName);
      navigate(`/batches/${batchName}`);
    } else {
      setSelectedBatchName(null);
      navigate("/batches");
    }
  }, [batchName, setSelectedBatchName, navigate]);

  // 返回列表
  const handleBackToList = useCallback(() => {
    setSelectedBatchName(null);
    navigate("/batches");
  }, [navigate, setSelectedBatchName]);

  // 處理雞種選擇變更的函數
  const handleBreedChange = useCallback(
    (breed: ChickenBreedType) => {
      setQueryParams({ ...queryParams, chickenBreed: breed });
      setBatchIndices([]);
    },
    [setQueryParams, setBatchIndices, queryParams]
  );

  // 處理完成狀態切換的函數
  const handleToggleIsCompleted = useCallback(() => {
    setQueryParams({ ...queryParams, isCompleted: !queryParams.isCompleted });
    setBatchIndices([]);
  }, [setQueryParams, queryParams, setBatchIndices]);

  // 處理排序順序切換的函數
  const handleToggleSortOrder = useCallback(() => {
    setQueryParams({
      ...queryParams,
      sortOrder: queryParams.sortOrder === "asc" ? "desc" : "asc",
    });
    setBatchIndices([]);
  }, [setQueryParams, queryParams, setBatchIndices]);

  // 處理日期範圍變更的函數
  const handleDateChange = useCallback(
    (start: Date | null, end: Date | null) => {
      // 將 null 轉換為 undefined，以符合 QueryParams 的類型
      const newStart = start === null ? undefined : start;
      const newEnd = end === null ? undefined : end;

      setQueryParams({ ...queryParams, start: newStart, end: newEnd });
      setBatchIndices([]);
    },
    [setQueryParams, queryParams, setBatchIndices]
  );

  // 使用 batch hook 取得批次彙總資料
  const {
    data: batchAggregates,
    isLoading,
    isError,
    error,
  } = useBatchAggregatesIndex(queryParams);

  // 處理批次卡片點擊的函數
  const handleCardClick = useCallback(
    (clickedBatchName: string) => {
      // 如果點擊的是當前已選中的批次，則取消選中
      // 否則選中該批次
      if (selectedBatchName === clickedBatchName) {
        setSelectedBatchName(null);
        navigate("/batches");
      } else {
        setSelectedBatchName(clickedBatchName);
        navigate(`/batches/${clickedBatchName}`);
      }
    },
    [setSelectedBatchName, selectedBatchName, navigate]
  );

  // 將批次索引資料存入 store
  useEffect(() => {
    if (batchAggregates && batchAggregates.length > 0) {
      // 使用 useRef 記錄前一次的值來避免無限循環
      const currentIndices = useBatchStore.getState().batchIndices;

      // 檢查是否有實際變化
      if (
        currentIndices.length !== batchAggregates.length ||
        !currentIndices.every(
          (item, index) =>
            item.batch_name === batchAggregates[index]?.batch_name
        )
      ) {
        setBatchIndices(batchAggregates);
      }
    }
  }, [batchAggregates, setBatchIndices]);

  // 準備導航欄內容
  const leftActions = selectedBatchName ? (
    <BackButton onClick={handleBackToList} iconOnly={true} title="返回列表" />
  ) : null;

  // 右側操作區域 - 設置按鈕
  const rightActions = (
    <Button
      variant="ghost"
      size="icon"
      onClick={() => navigate("/settings")}
      title="設置"
    >
      <Settings className="h-5 w-5" />
    </Button>
  );

  // 處理載入和錯誤狀態
  if (isError && error)
    return (
      <div className="container mx-auto p-4">
        <Alert variant="destructive" className="mb-4">
          <AlertTitle>錯誤</AlertTitle>
          <AlertDescription>
            載入錯誤：{error.message || "未知錯誤"}
          </AlertDescription>
        </Alert>
      </div>
    );

  return (
    <LoadingSpinner show={isLoading}>
      {/* 頁面頂部導航欄 */}
      <PageNavbar
        title={selectedBatchName ? `${selectedBatchName}` : "批次管理"}
        leftActions={leftActions}
        rightActions={rightActions}
      />

      <div className="container mx-auto p-4 lg:p-6">
        {/* 根據是否選中批次使用不同的布局 */}
        {selectedBatchName ? (
          // 選中批次時的詳情視圖布局
          <div className="flex flex-col lg:flex-row lg:gap-6">
            {/* 左側：列表區域 - 在移動裝置隱藏，在桌面版顯示 */}
            <div className="hidden lg:block lg:w-1/3 space-y-4">
              <Card>
                <CardHeader className="p-3 pb-0">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">篩選選項</CardTitle>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={toggleFilterMode}
                    >
                      <SlidersHorizontal className="w-4 h-4 mr-2" />
                      {showFullFilter ? "精簡模式" : "更多篩選"}
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="p-3">
                  <BatchFilters
                    handleBreedChange={handleBreedChange}
                    toggleIsCompleted={handleToggleIsCompleted}
                    toggleSortOrder={handleToggleSortOrder}
                    handleDateChange={handleDateChange}
                    totalCount={batchIndices.length}
                    compact={!showFullFilter}
                  />
                </CardContent>
              </Card>

              <div
                className="space-y-3 overflow-y-auto custom-scrollbar"
                style={{ maxHeight: "calc(100vh - 270px)" }}
              >
                {batchIndices.map((index) => (
                  <Card
                    key={index.batch_name}
                    className={`transition-all hover:shadow-md ${batchName === index.batch_name ? "ring-2 ring-primary" : ""}`}
                  >
                    <CardContent className="p-0">
                      <BatchCard
                        batchName={index.batch_name}
                        isSelected={batchName === index.batch_name}
                        onClick={() => handleCardClick(index.batch_name)}
                      />
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>

            {/* 右側：詳情區域 */}
            <div className="w-full lg:w-2/3">
              <Card
                className="overflow-y-auto custom-scrollbar"
                style={{ maxHeight: "calc(100vh - 120px)" }}
              >
                {selectedBatchName && selectedBatchAggregate ? (
                  <CardContent className="p-0">
                    <BatchDetailPanel
                      batch={selectedBatchAggregate}
                      onUpdateActivity={handleUpdateBatchActivity}
                    />
                  </CardContent>
                ) : (
                  <CardContent className="flex items-center justify-center h-40">
                    <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
                  </CardContent>
                )}
              </Card>
            </div>
          </div>
        ) : (
          // 未選中批次時的網格布局
          <div className="space-y-6">
            {/* 過濾器部分 */}
            <Card>
              <CardHeader className="p-3 pb-0">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg">批次管理</CardTitle>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={toggleFilterMode}
                  >
                    <SlidersHorizontal className="w-4 h-4 mr-2" />
                    {showFullFilter ? "精簡模式" : "更多篩選"}
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="p-3">
                <BatchFilters
                  handleBreedChange={handleBreedChange}
                  toggleIsCompleted={handleToggleIsCompleted}
                  toggleSortOrder={handleToggleSortOrder}
                  handleDateChange={handleDateChange}
                  totalCount={batchIndices.length}
                  compact={!showFullFilter}
                />
              </CardContent>
            </Card>

            {/* 網格列表 */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {isLoading ? (
                Array(6)
                  .fill(0)
                  .map((_, i) => (
                    <Card
                      key={i}
                      className="h-48 flex items-center justify-center animate-pulse"
                    >
                      <Loader2 className="w-6 h-6 text-muted-foreground animate-spin" />
                    </Card>
                  ))
              ) : batchIndices.length === 0 ? (
                <Card className="col-span-full p-8 text-center">
                  <CardContent className="flex flex-col items-center justify-center h-40">
                    <Filter className="w-12 h-12 text-muted-foreground mb-4" />
                    <p className="text-lg font-medium mb-2">
                      沒有符合條件的批次
                    </p>
                    <p className="text-muted-foreground">
                      請嘗試調整篩選條件或建立新批次
                    </p>
                  </CardContent>
                </Card>
              ) : (
                batchIndices.map((index) => (
                  <Card
                    key={index.batch_name}
                    className={`transition-all hover:shadow-md ${selectedBatchName === index.batch_name ? "ring-2 ring-primary" : ""}`}
                  >
                    <CardContent className="p-0">
                      <BatchCard
                        batchName={index.batch_name}
                        isSelected={selectedBatchName === index.batch_name}
                        onClick={() => handleCardClick(index.batch_name)}
                      />
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          </div>
        )}
      </div>
    </LoadingSpinner>
  );
};

export default BatchesPage;
