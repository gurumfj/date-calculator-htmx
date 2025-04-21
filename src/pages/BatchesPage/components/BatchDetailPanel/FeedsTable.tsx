/**
 * 批次飼料紀錄表格
 * Why: 讓用戶快速檢視與管理飼料消耗紀錄，追蹤成本與效率。
 *      飼料資料直接影響批次健康與成本分析。
 */
import React from "react";
// import { BatchAggregate } from "@app-types"; // 已無需直接型別
import CommonTable, {
  formatDate,
  ColumnType,
} from "@components/common/CommonTable";
import { FeedsSummaryCard } from "../BatchSummaryCards";
import { Badge } from "@/components/ui/badge";

import { BatchAggregateWithRows } from "@/types";

interface FeedRecordTableProps {
  batch: BatchAggregateWithRows;
}

// Why: 元件完全解耦於父層，直接根據全局狀態查詢資料，提升重用性
const FeedRecordTable: React.FC<FeedRecordTableProps> = ({ batch }) => {
  if (!batch || !batch.feeds || !Array.isArray(batch.feeds)) return null;

  const feedRecords = batch.feeds;

  // 按日期排序，最新的在前面
  const sortedFeedRecords = [...feedRecords].sort(
    (a, b) => new Date(b.feed_date).getTime() - new Date(a.feed_date).getTime()
  );

  // 定義列
  const columns: ColumnType[] = [
    {
      key: "feed_date",
      title: "日期",
      render: (value) => formatDate(value),
      mobileOptions: {
        position: "header",
        show: true,
      },
    },
    {
      key: "feed_manufacturer",
      title: "製造商",
      mobileOptions: {
        position: "header",
        show: true,
      },
    },
    {
      key: "feed_item",
      title: "飼料品項",
      mobileOptions: {
        position: "content",
        show: true,
        label: "飼料品項",
        span: 2,
      },
    },
    {
      key: "sub_location",
      title: "子位置",
      render: (value) => value || "-",
      mobileOptions: {
        position: "content",
        show: true,
        label: "子位置",
      },
    },
    {
      key: "feed_week",
      title: "週齡",
      render: (value) => value || "-",
      mobileOptions: {
        position: "content",
        show: true,
        label: "週齡",
      },
    },
    {
      key: "feed_additive",
      title: "添加物",
      render: (value) => value || "-",
      mobileOptions: {
        position: "content",
        show: true,
        label: "添加物",
      },
    },
    {
      key: "feed_remark",
      title: "備註",
      render: (value) => value || "-",
      mobileOptions: {
        position: "footer",
        show: true,
        label: "備註",
        span: 2,
      },
    },
    {
      key: "is_completed",
      title: "狀態",
      align: "center",
      render: (value) => (
        <Badge variant={value ? "success" : "secondary"}>
          {value ? "已完成" : "進行中"}
        </Badge>
      ),
      mobileOptions: {
        position: "status",
        show: true,
      },
    },
  ];

  return (
    <div className="space-y-6">
      <FeedsSummaryCard batch={batch} />
      <CommonTable
        title="飼料記錄"
        columns={columns}
        data={sortedFeedRecords}
        emptyText="無飼料記錄"
        mobileCardOptions={{
          titleField: "feed_manufacturer",
          subtitleField: "feed_date",
          statusField: "is_completed",
          footerField: "feed_remark",
        }}
      />
    </div>
  );
};

export default FeedRecordTable;
