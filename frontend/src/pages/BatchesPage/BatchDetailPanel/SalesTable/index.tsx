import React from "react";
import { BatchAggregate } from "@app-types";
import { calculateDayAge } from "@utils/dateUtils";
import { calculateBatchAggregate } from "@utils/batchCalculations";
import CommonTable, { formatDate, ColumnType } from "@components/common/CommonTable";
import { SalesSummaryCard } from "../../components/BatchSummaryCards";

interface SalesRawTableProps {
  batch: BatchAggregate;
}

const SalesRawTable: React.FC<SalesRawTableProps> = ({ batch }) => {
  // 計算批次聚合數據
  const batchAggregate = calculateBatchAggregate(batch);

  if (!batchAggregate.saleRecords || !Array.isArray(batchAggregate.saleRecords)) {
    return null;
  }

  const sortedSalesRecords = [...batchAggregate.saleRecords].sort(
    (a, b) => new Date(b.sale_date).getTime() - new Date(a.sale_date).getTime()
  );

  // 定義列
  const columns: ColumnType[] = [
    {
      key: "sale_date",
      title: "日期",
      render: (value) => formatDate(value).split("-").slice(1).join("-"),
    },
    {
      key: "customer",
      title: "客戶",
    },
    {
      key: "dayAge",
      title: "日齡",
      render: (value) => value.join(", "),
    },
    {
      key: "male_count",
      title: "公雞",
      align: "right",
      render: (value) => value || 0,
    },
    {
      key: "female_count",
      title: "母雞",
      align: "right",
      render: (value) => value || 0,
    },
    {
      key: "avgMaleWeight",
      title: "公均",
      align: "right",
      render: (value) => (value ? value.toFixed(2) : "-") + " 斤",
    },
    {
      key: "avgFemaleWeight",
      title: "母均",
      align: "right",
      render: (value) => (value ? value.toFixed(2) : "-") + " 斤",
    },
    {
      key: "male_price",
      title: "公價",
      align: "right",
      render: (value) => value || "-",
    },
    {
      key: "female_price",
      title: "母價",
      align: "right",
      render: (value) => value || "-",
    },
    {
      key: "total_weight",
      title: "總重",
      align: "right",
      render: (value) => (value ? value.toFixed(1) : "-") + " 斤",
    },
  ];

  // 移動端卡片渲染函數
  const renderMobileCard = (sale: any, index: number) => (
    <div key={index} className="bg-white p-3 rounded-xl shadow-sm">
      <div className="flex justify-between items-start mb-2">
        <div>
          <div className="text-sm font-medium">{sale.customer}</div>
          <div className="text-xs text-gray-500">
            {formatDate(sale.sale_date)}
          </div>
        </div>
        <div className="text-right">
          <div className="text-xs text-gray-500">日齡</div>
          <div className="text-sm">
            {calculateDayAge(
              batch.breeds[0].breed_date,
              new Date(sale.sale_date)
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-500">公雞:</span>
          <span>{sale.male_count || 0} 隻</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">母雞:</span>
          <span>{sale.female_count || 0} 隻</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">公均:</span>
          <span>{sale.avgMaleWeight?.toFixed(2) || "-"} 斤</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">母均:</span>
          <span>{sale.avgFemaleWeight?.toFixed(2) || "-"} 斤</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">公價:</span>
          <span>{sale.male_price || "-"}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">母價:</span>
          <span>{sale.female_price || "-"}</span>
        </div>
      </div>

      <div className="mt-2 pt-2 border-t border-gray-100 flex justify-between">
        <span className="text-gray-500 text-sm">總重:</span>
        <span className="font-medium text-sm">
          {sale.total_weight?.toFixed(1) || "-"} 斤
        </span>
      </div>
    </div>
  );

  // 渲染表格頁腳（聚合資料行）
  const renderFooter = () => (
    <tr className="bg-[#F9F9FB] font-medium">
      <td colSpan={3} className="px-4 py-2 text-sm">
        批次總計
      </td>
      <td className="px-4 py-2 text-right text-sm">
        {batchAggregate.chickens.totalMale}
      </td>
      <td className="px-4 py-2 text-right text-sm">
        {batchAggregate.chickens.totalFemale}
      </td>
      <td colSpan={5}></td>
    </tr>
  );

  return (
    <div className="space-y-6">
      <SalesSummaryCard batch={batch} />
      <CommonTable
        title="銷售記錄"
        columns={columns}
        data={sortedSalesRecords}
        renderMobileCard={renderMobileCard}
        renderFooter={renderFooter}
      />
    </div>
  );
};

export default SalesRawTable;
