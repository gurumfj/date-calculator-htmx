import React, { useEffect } from "react";

import { useFetchBatchAggregatesIndex } from "@/hooks/useFetchBatches";
import { BatchFilters } from "@/pages/BatchesPage/components/BatchFilters";
import { useBatchStore } from "@/pages/BatchesPage/store/useBatchStore";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import BatchActivityEdit from "./BatchActivityEdit";
import PageNavbar from "@/components/layout/components/PageNavbar";
import BatchFinalDateEdit from "./BatchFinalDateEdit";

const BatchEditPage: React.FC = () => {
  // 從 Zustand store 獲取篩選條件
  const { filter } = useBatchStore();

  const {
    data: batchIndexes,
    error,
    isLoading,
  } = useFetchBatchAggregatesIndex(filter);

  // const [pagination, setPagination] = React.useState({
  //   offset: 0,
  //   limit: 10,
  // });

  // 監聽 store filter 的變化以重置分頁
  useEffect(() => {
    // 當 filter 對象變化時 (不包括第一次渲染)
    // 需要一種方式來判斷是否是初始加載，或者接受 filter 變化時總是重置
    console.log("Filter changed, resetting pagination"); // Debug log
    // setPagination((prev) => ({ ...prev, offset: 0 }));
  }, [filter]); // 依賴於 store 的 filter 對象

  if (error) {
    return <p className="text-red-600">{error.message}</p>;
  }

  if (isLoading) {
    return <p>載入中...</p>;
  }

  if (!batchIndexes) {
    return <p>查無批次索引資料</p>;
  }

  return (
    // 使用 Tailwind 的 p-5 (相當於 20px padding) 作為容器邊距
    <div className="p-2">
      <PageNavbar title="批次索引 (Batch Aggregate Index)" />
      {/* 渲染篩選器元件 - 無需 props，它使用 store */}
      <div className="p-2">
        <BatchFilters />
      </div>
      {batchIndexes.length > 0 ? (
        <>
          {/* Desktop View: Table (hidden on mobile) */}
          <Table className="hidden md:table">
            {/* 在 md 及以上屏幕顯示表頭 */}
            <TableHeader className="hidden md:table-header-group">
              <TableRow>
                <TableHead>批次名稱</TableHead>
                <TableHead>品種</TableHead>
                <TableHead>起始日期</TableHead>
                <TableHead>最近異動日期</TableHead>
                <TableHead>更改狀態</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {batchIndexes.map((batch) => (
                // 桌面表格行樣式
                <TableRow
                  key={`${batch.batch_name}-desktop`}
                  className="md:table-row"
                >
                  <TableCell className="md:p-4">
                    {batch.batch_name ?? "N/A"}
                  </TableCell>
                  <TableCell className="md:p-4">
                    {batch.chicken_breed ?? "N/A"}
                  </TableCell>
                  <TableCell className="md:p-4">
                    {batch.initial_date ?? "N/A"}
                  </TableCell>
                  <TableCell className="md:p-4">
                    <BatchFinalDateEdit batchName={batch.batch_name} />
                  </TableCell>
                  <TableCell className="md:p-4">
                    <BatchActivityEdit batchName={batch.batch_name} />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>

          {/* Mobile View: Card List (hidden on desktop) */}
          <div className="md:hidden">
            {batchIndexes.map((batch) => (
              <div
                key={`${batch.batch_name}-mobile`}
                className="mb-4 rounded-lg border bg-card p-4 text-card-foreground shadow"
              >
                <div className="mb-2 flex justify-between">
                  <span className="font-bold">批次名稱:</span>
                  <span>{batch.batch_name ?? "N/A"}</span>
                </div>
                <div className="mb-2 flex justify-between">
                  <span className="font-semibold">品種:</span>
                  <span>{batch.chicken_breed ?? "N/A"}</span>
                </div>
                <div className="mb-2 flex justify-between">
                  <span className="font-semibold">起始日期:</span>
                  <span>{batch.initial_date ?? "N/A"}</span>
                </div>
                <div className="mb-3 flex items-center justify-between">
                  <span className="font-semibold">最近異動日期:</span>
                  <BatchFinalDateEdit batchName={batch.batch_name} />
                </div>
                <div className="flex items-center justify-between">
                  <span className="font-semibold">更改狀態:</span>
                  <BatchActivityEdit batchName={batch.batch_name} />
                </div>
              </div>
            ))}
          </div>
        </>
      ) : (
        <p>查無批次索引資料</p>
      )}
    </div>
  );
};

export default BatchEditPage;
