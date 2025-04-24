import React from "react";
import PageNavbar from "@/components/layout/components/PageNavbar";
import {
  useFetchBatchAggregates,
  useFetchBatchAggregatesIndex,
} from "@/hooks/useFetchBatches";
import { BatchFilters } from "../BatchesPage/components";
import CustomerWeightPieChart from "@/components/charts/CustomerWeightPieChart";
import { useBatchStore } from "../BatchesPage/store/useBatchStore";

const ReportsPage: React.FC = () => {
  // ================== 狀態與 hooks 定義區 ==================
  const { filter } = useBatchStore();
  // 1. React Query hooks
  const {
    data: batchIndice = [],
    isLoading,
    isError,
  } = useFetchBatchAggregatesIndex(filter);
  const { data: batchAggregates = [] } = useFetchBatchAggregates(
    batchIndice.map((b) => b.batch_name)
  );

  // PieChart 元件已封裝為 CustomerPie，提升可維護性與重用性

  // ================== 渲染區段 ==================
  if (isLoading) {
    return <div className="text-center p-4">載入中...</div>;
  }
  if (isError) {
    return <div className="text-center p-4">載入失敗</div>;
  }
  return (
    <>
      {/* 頁面頂部導航欄 */}
      <PageNavbar title="銷售報表" />

      <div className="p-2">
        <BatchFilters />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"></div>
        <div className="p-2">
          {/* PieChart 區塊元件化，減少主頁面複雜度 */}
          <CustomerWeightPieChart batchAggregates={batchAggregates} />
        </div>
      </div>
    </>
  );
};

export default ReportsPage;
