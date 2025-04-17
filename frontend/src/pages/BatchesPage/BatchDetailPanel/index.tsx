import React, { useState } from "react";
import FeedRecordTable from "./FeedsTable";
import {
  BatchAggregate,
  BatchActivity,
  BatchActivityOptions,
  CustomData,
} from "@app-types";
import { getBatchStateDisplay } from "@utils/batchCalculations";
import BatchDetail from "./BreedsTable";
import SalesRawTable from "./SalesTable";
import TodoistPage from "@pages/Todoist";
import { CheckCircleIcon, PencilIcon } from "@heroicons/react/24/outline";
import { Badge } from "@/components/ui/badge";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { BATCH_ACTIVITY_COLORS } from "@app-types";

// 擴展組件 props 接口
interface BatchDetailPanelProps {
  batch: BatchAggregate;
  onUpdateActivity?: (
    batchName: string,
    customData: CustomData,
    newActivity: BatchActivity
  ) => void;
}

const BatchDetailPanel: React.FC<BatchDetailPanelProps> = ({
  batch,
  onUpdateActivity,
}) => {
  // 編輯狀態管理
  const [isEditing, setIsEditing] = useState(false);
  const [selectedActivity, setSelectedActivity] = useState<BatchActivity>(
    batch.customData.batchActivity
  );
  const [isUpdating, setIsUpdating] = useState(false);

  // 使用計算工具函數確定批次活動
  const batchActivity = batch.customData.batchActivity;

  // 獲取活動的顯示樣式
  const activityDisplay = getBatchStateDisplay(batchActivity);

  // 確定哪些標籤頁應該顯示
  const hasSales = batch.sales && batch.sales.length > 0;
  const hasFeeds = batch.feeds && batch.feeds.length > 0;

  // 處理狀態更新
  const handleUpdateBatchActivity = () => {
    if (selectedActivity === batchActivity) {
      setIsEditing(false);
      return;
    }

    setIsUpdating(true);

    // 如果存在父組件提供的更新函數，則使用它
    if (onUpdateActivity) {
      onUpdateActivity(
        batch.batchIndex.batch_name,
        batch.customData,
        selectedActivity
      );
      setIsEditing(false);
      setIsUpdating(false);
    } else {
      // 如果沒有提供更新函數，最後也要重置狀態
      console.error("未提供更新函數");
      setIsEditing(false);
      setIsUpdating(false);
    }
  };

  // 取消編輯
  const handleCancelEdit = () => {
    setSelectedActivity(batchActivity);
    setIsEditing(false);
  };

  return (
    <Card className="h-full flex flex-col overflow-hidden rounded-none border-l shadow-none border-r-0 border-t-0 border-b-0">
      <CardHeader className="p-4 border-b">
        <div className="flex justify-between items-center">
          <CardTitle className="text-xl font-semibold text-[#1C1C1E]">
            {batch.batchIndex.batch_name} 詳細資訊
          </CardTitle>

          {isEditing ? (
            <div className="flex items-center space-x-2">
              <Select
                value={selectedActivity}
                onValueChange={(value: BatchActivity) =>
                  setSelectedActivity(value)
                }
                disabled={isUpdating}
              >
                <SelectTrigger className="w-36 h-8 text-xs">
                  <SelectValue placeholder="選擇批次活動" />
                </SelectTrigger>
                <SelectContent>
                  {BatchActivityOptions.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Button
                variant="ghost"
                size="sm"
                onClick={handleCancelEdit}
                disabled={isUpdating}
                className="h-8 px-2"
              >
                取消
              </Button>

              <Button
                size="sm"
                onClick={handleUpdateBatchActivity}
                disabled={isUpdating}
                className="h-8 px-2 bg-[#007AFF] hover:bg-[#0062CC] text-white"
              >
                {isUpdating ? "更新中..." : "確認"}
              </Button>
            </div>
          ) : (
            <div className="flex items-center">
              <Badge
                data-batch-activity
                style={{
                  backgroundColor: BATCH_ACTIVITY_COLORS[batchActivity].bg,
                  color: "white",
                }}
                className="rounded-md text-xs font-medium mr-2"
              >
                {activityDisplay.label}
              </Badge>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setIsEditing(true)}
                className="h-7 w-7 rounded-full hover:bg-gray-100"
                title="編輯批次活動"
              >
                <PencilIcon className="h-4 w-4 text-gray-500" />
              </Button>
            </div>
          )}
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
              <BatchDetail batch={batch} />
            </TabsContent>

            {hasSales && (
              <TabsContent value="sales" className="p-0 m-0 h-full">
                <SalesRawTable batch={batch} />
              </TabsContent>
            )}

            {hasFeeds && (
              <TabsContent value="feeds" className="p-0 m-0 h-full">
                <FeedRecordTable batch={batch} />
              </TabsContent>
            )}

            <TabsContent value="todos" className="p-0 m-0 h-full">
              <TodoistPage batch={batch} />
            </TabsContent>
          </div>
        </Tabs>
      </CardContent>
    </Card>
  );
};

export default BatchDetailPanel;
