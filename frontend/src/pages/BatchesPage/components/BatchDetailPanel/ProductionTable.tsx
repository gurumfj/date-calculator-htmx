/**
 * 批次結案成本詳細表格
 * Why: 集中顯示單一批次的結案成本詳細數據，包括各項成本和費用的細項分析。
 *      支援成本結構分析與成本控制決策。
 */
import React from "react";
import CommonTable, { ColumnType } from "@components/common/CommonTable";
import { Card, CardContent } from "@/components/ui/card";
import { BatchAggregateWithRows } from "@app-types";
import { formatCurrency } from "@utils/formatUtils";

export interface ProductionTableProps {
  batch: BatchAggregateWithRows;
}

export const ProductionTable: React.FC<ProductionTableProps> = ({ batch }) => {
  if (!batch.production || batch.production.length === 0) {
    return (
      <Card>
        <CardContent className="p-4 text-center">
          <div className="text-sm text-muted-foreground">無結案資料</div>
        </CardContent>
      </Card>
    );
  }

  // 定義列
  const columns: ColumnType[] = [
    {
      key: "expenses",
      title: "總支出",
      render: (value) => formatCurrency(value),
      mobileOptions: {
        position: "status",
        show: true,
        label: "總支出",
      },
    },
    {
      key: "chick_cost",
      title: "雛雞成本",
      render: (value) => formatCurrency(value),
      mobileOptions: {
        position: "content",
        show: true,
        label: "雛雞成本",
      },
    },
    {
      key: "feed_cost",
      title: "飼料成本",
      render: (value) => formatCurrency(value),
      mobileOptions: {
        position: "content",
        show: true,
        label: "飼料成本",
      },
    },
    {
      key: "feed_med_cost",
      title: "飼料藥物成本",
      render: (value) => formatCurrency(value),
      mobileOptions: {
        position: "content",
        show: true,
        label: "飼料藥物成本",
      },
    },
    {
      key: "farm_med_cost",
      title: "農場藥物成本",
      render: (value) => formatCurrency(value),
      mobileOptions: {
        position: "content",
        show: true,
        label: "農場藥物成本",
      },
    },
    {
      key: "grow_fee",
      title: "飼養費用",
      render: (value) => formatCurrency(value),
      mobileOptions: {
        position: "content",
        show: true,
        label: "飼養費用",
      },
    },
    {
      key: "catch_fee",
      title: "捕捉費用",
      render: (value) => formatCurrency(value),
      mobileOptions: {
        position: "content",
        show: true,
        label: "捕捉費用",
      },
    },
    {
      key: "weigh_fee",
      title: "稱重費用",
      render: (value) => formatCurrency(value),
      mobileOptions: {
        position: "content",
        show: true,
        label: "稱重費用",
      },
    },
    {
      key: "leg_band_cost",
      title: "腳環成本",
      render: (value) => formatCurrency(value),
      mobileOptions: {
        position: "content",
        show: true,
        label: "腳環成本",
      },
    },
    {
      key: "meat_cost",
      title: "肉品成本",
      render: (value) => formatCurrency(value),
      mobileOptions: {
        position: "content",
        show: true,
        label: "肉品成本",
      },
    },
    {
      key: "vet_cost",
      title: "獸醫成本",
      render: (value) => formatCurrency(value),
      mobileOptions: {
        position: "content",
        show: true,
        label: "獸醫成本",
      },
    },
    {
      key: "gas_cost",
      title: "瓦斯成本",
      render: (value) => formatCurrency(value),
      mobileOptions: {
        position: "content",
        show: true,
        label: "瓦斯成本",
      },
    },
  ];

  return (
    <CommonTable
      title="成本詳細"
      columns={columns}
      data={batch.production}
      emptyText="無成本詳細資料"
      mobileCardOptions={{
        // titleField: "batch_name",
        // subtitleField: "created_at",
        // statusField: "created_at",
        // statusLabel: "完成日期",
        footerField: "expenses",
        footerLabel: "總支出",
      }}
    />
  );
};

export default ProductionTable;
