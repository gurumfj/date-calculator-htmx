/**
 * 批次詳細資訊面板
 * Why: 統一管理批次下的多個子表格（品種、飼料、銷售等），
 *      以分頁方式提升可讀性與維護性，並解耦父子元件狀態。
 */
import React from "react";
import FeedRecordTable from "./FeedsTable";
import SalesTable from "./SalesTable";
import TodoistPage from "@pages/Todoist";
import { CheckCircleIcon } from "@heroicons/react/24/outline";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { useBatchStore } from "@pages/BatchesPage/store/useBatchStore";
import { useFetchBatchAggregates } from "@/hooks/useFetchBatches";
import { BreedSummaryCard } from "../BatchSummaryCards";
import { BreedsTable } from "./BreedsTable";
import CustomerWeightPieChart from "@/components/charts/CustomerWeightChart";
import CustomerCountChart from "@/components/charts/CustomerCountChart";

// Why: 解耦父子元件，直接從 store 取得狀態，提升可重用性
const BatchDetailPanel: React.FC = () => {
  // Why: 單一來源原則，所有 UI 狀態與資料皆從 store 取得
  const selectedBatchName = useBatchStore((s) => s.selectedBatchName);
  const { data: batchAggregates, isLoading } = useFetchBatchAggregates([
    selectedBatchName || "",
  ]);

  const batchAggregate = batchAggregates?.[0];
  const hasSales =
    Array.isArray(batchAggregate?.sales) && batchAggregate.sales.length > 0;
  const hasFeeds =
    Array.isArray(batchAggregate?.feeds) && batchAggregate.feeds.length > 0;

  if (isLoading) {
    return <div>loading...</div>;
  }

  if (!batchAggregate) {
    return <div>找不到批次資料</div>;
  }

  return (
    <Card className="h-full flex flex-col overflow-hidden rounded-none border-l shadow-none border-r-0 border-t-0 border-b-0">
      <CardHeader className="p-4 border-b">
        <div className="flex justify-between items-center">
          <CardTitle className="text-xl font-semibold text-[#1C1C1E]">
            {selectedBatchName}
          </CardTitle>
        </div>
      </CardHeader>

      <CardContent className="flex-1 overflow-y-auto p-0">
        <Tabs defaultValue="info" className="h-full flex flex-col">
          <TabsList className="flex justify-start space-x-2 rounded-none bg-[#F2F2F7] p-2 px-4 mb-0 sticky top-0 z-10 w-full">
            <TabsTrigger
              value="info"
              className="rounded-lg data-[state=active]:text-[#007AFF]"
            >
              批次資訊
            </TabsTrigger>

            {hasSales && (
              <TabsTrigger
                value="sales"
                className="rounded-lg data-[state=active]:text-[#007AFF]"
              >
                銷售
              </TabsTrigger>
            )}
            {hasSales && (
              <TabsTrigger
                value="sales-pie"
                className="rounded-lg data-[state=active]:text-[#007AFF]"
              >
                銷售圖表
              </TabsTrigger>
            )}

            {hasFeeds && (
              <TabsTrigger
                value="feeds"
                className="rounded-lg data-[state=active]:text-[#007AFF]"
              >
                飼料
              </TabsTrigger>
            )}

            <TabsTrigger
              value="todos"
              className="rounded-lg data-[state=active]:text-[#007AFF] flex items-center"
            >
              <CheckCircleIcon className="w-4 h-4 mr-1" />
              待辦事項
            </TabsTrigger>
          </TabsList>

          <div className="flex-1 p-4 overflow-y-auto">
            <TabsContent value="info" className="p-0 m-0 h-full">
              {/* Why: 子元件自行根據 selectedBatchName 查詢資料，提升元件解耦性 */}
              <div className="space-y-6">
                <BreedSummaryCard batch={batchAggregate} />
                <BreedsTable batch={batchAggregate} />
              </div>
            </TabsContent>

            {hasSales && (
              <TabsContent value="sales" className="p-0 m-0 h-full">
                <SalesTable batch={batchAggregate} />
              </TabsContent>
            )}
            {hasSales && (
              <TabsContent value="sales-pie" className="p-0 m-0 h-full">
                {/* TODO: 需要一層 charts-section 包裹 */}

                <CustomerCountChart batchAggregates={[batchAggregate]} />
                <CustomerWeightPieChart batchAggregates={[batchAggregate]} />
              </TabsContent>
            )}

            {hasFeeds && (
              <TabsContent value="feeds" className="p-0 m-0 h-full">
                <FeedRecordTable batch={batchAggregate} />
              </TabsContent>
            )}

            <TabsContent value="todos" className="p-0 m-0 h-full">
              {/* Why: 子元件自行根據 selectedBatchName 查詢資料，提升元件解耦性 */}
              <TodoistPage batch={batchAggregate} />
            </TabsContent>
          </div>
        </Tabs>
      </CardContent>
    </Card>
  );
};

export default BatchDetailPanel;
