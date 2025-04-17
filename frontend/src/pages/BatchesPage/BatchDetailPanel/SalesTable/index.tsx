import React from "react";
import { BatchAggregate } from "@app-types";
import { calculateBatchAggregate } from "@utils/batchCalculations";
import CommonTable, { formatDate, ColumnType } from "@components/common/CommonTable";
import { SalesSummaryCard } from "../../components/BatchSummaryCards";
import { TableRow, TableCell } from "@/components/ui/table";

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
      mobileOptions: {
        position: "header",
        show: true,
      }
    },
    {
      key: "customer",
      title: "客戶",
      mobileOptions: {
        position: "header",
        show: true,
      }
    },
    {
      key: "dayAge",
      title: "日齡",
      render: (value) => value.join(", "),
      mobileOptions: {
        position: "status",
        show: true,
        label: "日齡"
      }
    },
    {
      key: "male_count",
      title: "公雞",
      align: "right",
      render: (value) => value || 0,
      mobileOptions: {
        position: "content",
        show: true,
        label: "公雞"
      }
    },
    {
      key: "female_count",
      title: "母雞",
      align: "right",
      render: (value) => value || 0,
      mobileOptions: {
        position: "content",
        show: true,
        label: "母雞"
      }
    },
    {
      key: "avgMaleWeight",
      title: "公均",
      align: "right",
      render: (value) => (value ? value.toFixed(2) : "-") + " 斤",
      mobileOptions: {
        position: "content",
        show: true,
        label: "公均"
      }
    },
    {
      key: "avgFemaleWeight",
      title: "母均",
      align: "right",
      render: (value) => (value ? value.toFixed(2) : "-") + " 斤",
      mobileOptions: {
        position: "content",
        show: true,
        label: "母均"
      }
    },
    {
      key: "male_price",
      title: "公價",
      align: "right",
      render: (value) => value || "-",
      mobileOptions: {
        position: "content",
        show: true,
        label: "公價"
      }
    },
    {
      key: "female_price",
      title: "母價",
      align: "right",
      render: (value) => value || "-",
      mobileOptions: {
        position: "content",
        show: true,
        label: "母價"
      }
    },
    {
      key: "total_weight",
      title: "總重",
      align: "right",
      render: (value) => (value ? value.toFixed(1) : "-") + " 斤",
      mobileOptions: {
        position: "footer",
        show: true,
        label: "總重"
      }
    },
  ];

  // 渲染表格頁腳（聚合資料行）
  const renderFooter = () => (
    <TableRow className="font-medium">
      <TableCell colSpan={3}>批次總計</TableCell>
      <TableCell className="text-right">
        {batchAggregate.chickens.totalMale}
      </TableCell>
      <TableCell className="text-right">
        {batchAggregate.chickens.totalFemale}
      </TableCell>
      <TableCell colSpan={5}></TableCell>
    </TableRow>
  );

  return (
    <div className="space-y-6">
      <SalesSummaryCard batch={batch} />
      <CommonTable
        title="銷售記錄"
        columns={columns}
        data={sortedSalesRecords}
        renderFooter={renderFooter}
        mobileCardOptions={{
          titleField: "customer",
          subtitleField: "sale_date",
          statusField: "dayAge",
          statusLabel: "日齡",
          footerField: "total_weight",
          footerLabel: "總重"
        }}
      />
    </div>
  );
};

export default SalesRawTable;
