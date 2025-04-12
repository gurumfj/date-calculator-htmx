import React from "react";
import { BatchAggregate, FeedRecordRow } from "@app-types";
import CommonTable, { formatDate, ColumnType } from "@components/common/CommonTable";
import { FeedsSummaryCard } from "../../components/BatchSummaryCards";

interface FeedRecordTableProps {
  batch: BatchAggregate;
}

const FeedRecordTable: React.FC<FeedRecordTableProps> = ({ batch }) => {
  const feedRecords = batch.feeds || [];

  if (!feedRecords || !Array.isArray(feedRecords)) return null;

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
    },
    {
      key: "feed_manufacturer",
      title: "製造商",
    },
    {
      key: "feed_item",
      title: "飼料品項",
    },
    {
      key: "sub_location",
      title: "子位置",
      render: (value) => value || "-",
    },
    {
      key: "feed_week",
      title: "週齡",
      render: (value) => value || "-",
    },
    {
      key: "feed_additive",
      title: "添加物",
      render: (value) => value || "-",
    },
    {
      key: "feed_remark",
      title: "備註",
      render: (value) => value || "-",
    },
    {
      key: "is_completed",
      title: "狀態",
      align: "center",
      render: (value) => (
        <span
          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
            value
              ? "bg-green-100 text-green-800"
              : "bg-yellow-100 text-yellow-800"
          }`}
        >
          {value ? "已完成" : "進行中"}
        </span>
      ),
    },
  ];

  // 移動端卡片渲染函數
  const renderMobileCard = (feed: FeedRecordRow, index: number) => (
    <div key={index} className="bg-white p-3 rounded-xl shadow-sm">
      <div className="flex justify-between items-start mb-2">
        <div>
          <div className="text-sm font-medium">{feed.feed_manufacturer}</div>
          <div className="text-xs text-gray-500">{formatDate(feed.feed_date)}</div>
        </div>
        <div className="text-right">
          <span
            className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
              feed.is_completed
                ? "bg-green-100 text-green-800"
                : "bg-yellow-100 text-yellow-800"
            }`}
          >
            {feed.is_completed ? "已完成" : "進行中"}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2 text-sm mt-2">
        <div className="flex justify-between">
          <span className="text-gray-500">飼料品項:</span>
          <span className="font-medium">{feed.feed_item}</span>
        </div>
        {feed.sub_location && (
          <div className="flex justify-between">
            <span className="text-gray-500">子位置:</span>
            <span>{feed.sub_location}</span>
          </div>
        )}
        {feed.feed_week && (
          <div className="flex justify-between">
            <span className="text-gray-500">週齡:</span>
            <span>{feed.feed_week}</span>
          </div>
        )}
        {feed.feed_additive && (
          <div className="flex justify-between">
            <span className="text-gray-500">添加物:</span>
            <span>{feed.feed_additive}</span>
          </div>
        )}
      </div>

      {feed.feed_remark && (
        <div className="mt-2 pt-2 border-t border-gray-100">
          <div className="text-xs text-gray-500 mb-1">備註</div>
          <div className="text-sm">{feed.feed_remark}</div>
        </div>
      )}
    </div>
  );

  return (
    <div className="space-y-6">
      <FeedsSummaryCard batch={batch} />
      <CommonTable
        title="飼料記錄"
        columns={columns}
        data={sortedFeedRecords}
        renderMobileCard={renderMobileCard}
        emptyText="無飼料記錄"
      />
    </div>
  );
};

export default FeedRecordTable;
