import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  Cell,
  ResponsiveContainer,
} from "recharts";
import { BatchAggregateWithRows } from "@/types";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from "@/components/ui/card";
import { ChartContainer } from "@/components/ui/chart";

const BAR_COLORS = [
  "hsl(var(--chart-1))",
  "hsl(var(--chart-2))",
  "hsl(var(--chart-3))",
  "hsl(var(--chart-4))",
  "hsl(var(--chart-5))",
  "hsl(var(--chart-6))",
];

interface CustomerWeightPieChartProps {
  batchAggregates: BatchAggregateWithRows[];
}

/**
 * 顯示客戶分組加總重量的 Bar Chart，橫式顯示所有客戶
 * Why: 橫式長條圖更適合大量分類資料，提升可讀性
 */

const CustomerWeightPieChart: React.FC<CustomerWeightPieChartProps> = ({
  batchAggregates,
}) => {
  /**
   * 將 batchAggregates 依據 sales.customer 分組加總重量，並回傳 Chart 需要的格式
   * Why: 使用單一 reduce 迭代減少運算次數，提升效能
   */
  const totalWeightByCustomer = (batchAggregates: BatchAggregateWithRows[]) => {
    // 如果沒有資料，直接回傳空陣列
    if (!batchAggregates?.length) return [];
    
    const allSales = batchAggregates.flatMap((batch) => batch.sales || []);
    if (!allSales.length) return [];
    
    // Why: 使用單一 reduce 同時計算總重量與客戶分組
    const { totalWeight, customerWeightMap } = allSales.reduce(
      (acc, sale) => {
        const weight = sale.total_weight || 0;
        const customer = sale.customer || "未知客戶";
        
        // 累計總重量
        acc.totalWeight += weight;
        
        // 客戶分組累計
        const existingWeight = acc.customerWeightMap.get(customer) || 0;
        acc.customerWeightMap.set(customer, existingWeight + weight);
        
        return acc;
      },
      { totalWeight: 0, customerWeightMap: new Map<string, number>() }
    );
    
    // 轉換為需要的返回格式並排序
    return Array.from(customerWeightMap.entries())
      .map(([name, weight]) => ({
        name,
        weight,
        percentage: totalWeight > 0 ? weight / totalWeight : 0,
      }))
      .sort((a, b) => b.weight - a.weight);
  };

  // Why: 所有依 batchAggregates 聚合、排序、日期區間的運算整合於單一 useMemo，提升效能
  const { customerData, dynamicHeight, startDate, endDate } =
    React.useMemo(() => {
      const customerData = totalWeightByCustomer(batchAggregates);
      const dynamicHeight = Math.max(
        400,
        Math.min(1000, customerData.length * 40)
      );
      const sales = batchAggregates.flatMap((b) => b.sales);
      const sortedSales = [...sales].sort(
        (a, b) =>
          new Date(a.sale_date).getTime() - new Date(b.sale_date).getTime()
      );
      const startDate = sortedSales.length
        ? new Date(sortedSales[0].sale_date)
        : null;
      const endDate = sortedSales.length
        ? new Date(sortedSales[sortedSales.length - 1].sale_date)
        : null;
      return { customerData, dynamicHeight, startDate, endDate };
    }, [batchAggregates]);

  // Why: 增強空資料處理，檢查多種邊界情況
  if (!startDate || !endDate || !customerData.length) {
    return <div className="text-center p-4">無可用的銷售資料</div>;
  }

  return (
    <Card className="flex flex-col">
      <CardHeader className="pb-2">
        <CardTitle>客戶重量排行</CardTitle>
        <CardDescription>
          {startDate?.toISOString().split("T")[0]} ~{" "}
          {endDate?.toISOString().split("T")[0]}
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-2 flex-1 pb-0">
        {/* Why: Bar Chart 置中，依據資料數量動態調整高度 */}
        <div className="w-full flex justify-center">
          <ChartContainer
            className="w-full"
            style={{ minHeight: dynamicHeight }}
            config={{}}
          >
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={customerData}
                layout="vertical"
                margin={{ top: 16, right: 32, left: 32, bottom: 16 }}
                barCategoryGap={8}
              >
                <XAxis
                  type="number"
                  dataKey="weight"
                  tickFormatter={(v) => `${Math.round(v)}kg`}
                  axisLine={false}
                  tickLine={false}
                  stroke="#888"
                />
                <YAxis
                  type="category"
                  dataKey="name"
                  interval={0}
                  width={60}
                  tickLine={false}
                  axisLine={false}
                  stroke="#888"
                />
                <Tooltip
                  formatter={(value: number) =>
                    `${Math.round(value as number)} kg`
                  }
                  contentStyle={{
                    background: document.documentElement.classList.contains(
                      "dark"
                    )
                      ? "#222"
                      : "#fff",
                    color: document.documentElement.classList.contains("dark")
                      ? "#f3f3f3"
                      : "#333",
                    borderRadius: 8,
                  }}
                  itemStyle={{
                    color: document.documentElement.classList.contains("dark")
                      ? "#f3f3f3"
                      : "#333",
                  }}
                />
                <Legend
                  verticalAlign="bottom"
                  height={36}
                  wrapperStyle={{
                    color: document.documentElement.classList.contains("dark")
                      ? "#f3f3f3"
                      : "#333",
                  }}
                />
                <Bar dataKey="weight" radius={[8, 8, 8, 8]}>
                  {customerData.map((entry, idx) => (
                    <Cell
                      key={entry.name}
                      fill={BAR_COLORS[idx % BAR_COLORS.length]}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </ChartContainer>
        </div>
      </CardContent>
      <CardFooter className="flex-col gap-2 text-sm"></CardFooter>
    </Card>
  );
};

export default CustomerWeightPieChart;
