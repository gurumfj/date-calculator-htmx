/**
 * 客戶數量圖表元件
 * 使用人口金字塔式圖表展示客戶的公雞和母雞數量分布
 * 支持按公雞數量、母雞數量或總數量排序
 */

import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
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
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { SortDescIcon } from "lucide-react";
import { ChartContainer } from "@/components/ui/chart";

// 定義圖表顏色常數
const MALE_COLOR = "hsl(var(--chart-2))"; // 公雞顏色
const FEMALE_COLOR = "hsl(var(--chart-1))"; // 母雞顏色

// 排序選項類型
type SortOption = "male" | "female" | "total";

// 客戶數據類型
interface CustomerData {
  customer: string;
  maleCount: number;
  femaleCount: number;
  originalMaleCount: number; // 存儲原始數值供排序使用
}

// 組件屬性
interface CustomerCountChartProps {
  batchAggregates: BatchAggregateWithRows[];
}

/**
 * 客戶數量圖表組件
 * 使用人口金字塔式圖表展示客戶的公雞和母雞數量分布
 */
const CustomerCountChart: React.FC<CustomerCountChartProps> = ({
  batchAggregates,
}) => {
  // 管理排序選項的狀態，默認按公雞數量排序
  const [sortBy, setSortBy] = React.useState<SortOption>("male");
  /**
   * 轉換批次資料為客戶數量統計
   * @param batchAggregates 批次資料陣列
   * @returns 客戶數量統計陣列
   */
  const totalCountByCustomer = (
    batchAggregates: BatchAggregateWithRows[]
  ): CustomerData[] => {
    // 資料有效性檢查
    if (!batchAggregates?.length) return [];

    // 將所有批次的銷售資料合併為一個平面陣列
    const allSales = batchAggregates.flatMap((batch) => batch.sales || []);
    if (!allSales.length) return [];

    // 使用 Map 對客戶進行分組累計
    const { customerCountMap } = allSales.reduce(
      (acc, sale) => {
        const male = sale.male_count || 0;
        const female = sale.female_count || 0;
        const customer = sale.customer || "未知客戶";

        // 累加到客戶統計中
        const existingMaleCount = acc.customerCountMap.get(customer)?.male || 0;
        const existingFemaleCount =
          acc.customerCountMap.get(customer)?.female || 0;
        acc.customerCountMap.set(customer, {
          male: existingMaleCount + male,
          female: existingFemaleCount + female,
        });

        return acc;
      },
      { customerCountMap: new Map<string, { male: number; female: number }>() }
    );

    // 轉換為圖表所需的數據格式
    return Array.from(customerCountMap.entries()).map(
      ([customer, { male, female }]) => ({
        customer,
        maleCount: -Math.abs(male), // 公雞數量轉為負數，用於金字塔圖表
        femaleCount: female,
        originalMaleCount: male, // 保存原始正數值供排序使用
      })
    );
  };

  /**
   * 計算圖表所需的各種數據
   * 將所有計算整合到一個 useMemo 中，提高效能
   */
  const {
    customerData,
    totalMale,
    totalFemale,
    dynamicHeight,
    startDate,
    endDate,
  } = React.useMemo(() => {
    // 1. 獲取客戶數據
    let customerData = totalCountByCustomer(batchAggregates);

    // 2. 根據選擇的排序方式進行排序
    customerData = [...customerData].sort((a, b) => {
      switch (sortBy) {
        case "male":
          // 按公雞數量降序排列
          return Math.abs(b.originalMaleCount) - Math.abs(a.originalMaleCount);
        case "female":
          // 按母雞數量降序排列
          return b.femaleCount - a.femaleCount;
        case "total":
        default:
          // 按總數量降序排列
          return (
            Math.abs(b.originalMaleCount) +
            b.femaleCount -
            (Math.abs(a.originalMaleCount) + a.femaleCount)
          );
      }
    });

    // 3. 計算圖表高度，根據客戶數量動態調整
    const dynamicHeight = Math.max(
      400, // 最小高度
      Math.min(1000, customerData.length * 40) // 每個客戶分配 40px，但不超過 1000px
    );

    // 4. 計算日期範圍
    const sales = batchAggregates.flatMap((b) => b.sales || []);
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

    // 5. 計算公雞和母雞的總數量
    const totalMale = customerData.reduce(
      (sum, item) => sum + Math.abs(item.originalMaleCount),
      0
    );
    const totalFemale = customerData.reduce(
      (sum, item) => sum + item.femaleCount,
      0
    );

    return {
      customerData,
      totalMale,
      totalFemale,
      dynamicHeight,
      startDate,
      endDate,
    };
  }, [batchAggregates, sortBy]); // 依賴項包括批次數據和排序選項

  /**
   * 空資料處理
   * 檢查多種邊界情況，確保圖表只在有有效數據時才渲染
   */
  if (!startDate || !endDate || !customerData.length) {
    return <div className="text-center p-4">無可用的銷售資料</div>;
  }

  return (
    <Card className="flex flex-col">
      <CardHeader className="pb-2">
        <div className="flex justify-between items-center">
          <CardTitle>客戶數量排行</CardTitle>
          {/* 排序選項切換器 */}
          <ToggleGroup
            type="single"
            value={sortBy}
            onValueChange={(value) => value && setSortBy(value as SortOption)}
          >
            <ToggleGroupItem
              value="male"
              aria-label="按公雞數量排序"
              className="flex items-center gap-1"
            >
              <span>公雞</span>
              <SortDescIcon className="h-4 w-4" />
            </ToggleGroupItem>
            <ToggleGroupItem
              value="female"
              aria-label="按母雞數量排序"
              className="flex items-center gap-1"
            >
              <span>母雞</span>
              <SortDescIcon className="h-4 w-4" />
            </ToggleGroupItem>
            <ToggleGroupItem
              value="total"
              aria-label="按總數量排序"
              className="flex items-center gap-1"
            >
              <span>總數</span>
              <SortDescIcon className="h-4 w-4" />
            </ToggleGroupItem>
          </ToggleGroup>
        </div>
        {/* 日期範圍顯示 */}
        <CardDescription>
          {startDate?.toISOString().split("T")[0]} ~{" "}
          {endDate?.toISOString().split("T")[0]}
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-2 flex-1 pb-0">
        <div className="w-full flex justify-center">
          {/* 圖表容器，根據客戶數量動態調整高度 */}
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
                barGap={0} // 確保公雞和母雞柱狀圖線接
              >
                {/* X軸設置 - 數值軸 */}
                <XAxis
                  type="number"
                  tickFormatter={(v) => `${Math.abs(Math.round(v))}隻`} // 顯示絕對值
                  axisLine={true}
                  tickLine={true}
                  stroke="#888"
                  domain={["dataMin", "dataMax"]} // 自動調整軸範圍
                  padding={{ left: 20, right: 20 }} // 增加空間使圖表更易讀
                />

                {/* Y軸設置 - 客戶名稱 */}
                <YAxis
                  type="category"
                  dataKey="customer"
                  interval={0} // 顯示所有客戶名稱
                  width={60}
                  tickLine={false}
                  axisLine={false}
                  stroke="#888"
                />

                {/* 提示工具設置 */}
                <Tooltip
                  formatter={(value: number, name) => {
                    const absValue = Math.abs(Math.round(value as number));
                    return `${absValue} 隻${name === "公雞" ? "公雞" : "母雞"}`;
                  }}
                  labelFormatter={(label) => `${label}`}
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

                {/* 圖例設置 */}
                <Legend
                  verticalAlign="bottom"
                  height={36}
                  wrapperStyle={{
                    color: document.documentElement.classList.contains("dark")
                      ? "#f3f3f3"
                      : "#333",
                  }}
                />

                {/* 0值參考線 - 區分公雞和母雞區域 */}
                <ReferenceLine x={0} stroke="#888" strokeDasharray="3 3" />

                {/* 公雞數量柱狀圖 - 負值區域 */}
                <Bar
                  dataKey="maleCount"
                  name="公雞"
                  radius={[0, 8, 8, 0]} // 右側圓角
                  fill={MALE_COLOR}
                  label={{
                    formatter: (value: number) =>
                      `${Math.abs(Math.round(value))}`,
                    fill: "#fff", // 白色文字增強可讀性
                    fontSize: 11,
                    offset: 10, // 往內偏移使標籤位於柱狀圖內
                  }}
                />

                {/* 母雞數量柱狀圖 - 正值區域 */}
                <Bar
                  dataKey="femaleCount"
                  name="母雞"
                  radius={[0, 8, 8, 0]} // 右側圓角
                  fill={FEMALE_COLOR}
                  label={{
                    position: "insideRight",
                    formatter: (value: number) => `${Math.round(value)}`,
                    fill: "#fff", // 白色文字增強可讀性
                    fontSize: 11,
                    offset: 10, // 往內偏移使標籤位於柱狀圖內
                  }}
                />
              </BarChart>
            </ResponsiveContainer>
          </ChartContainer>
        </div>
      </CardContent>
      {/* 總計數據展示區 */}
      <CardFooter className="flex justify-between items-center pt-2 border-t text-sm">
        {/* 公雞總數 */}
        <div className="flex items-center gap-2">
          <span className="font-semibold">公雞總數：</span>
          <span
            className="px-2 py-1 bg-muted rounded-md"
            style={{ color: MALE_COLOR }}
          >
            {totalMale} 隻
          </span>
        </div>

        {/* 母雞總數 */}
        <div className="flex items-center gap-2">
          <span className="font-semibold">母雞總數：</span>
          <span
            className="px-2 py-1 bg-muted rounded-md"
            style={{ color: FEMALE_COLOR }}
          >
            {totalFemale} 隻
          </span>
        </div>

        {/* 總計數量 */}
        <div className="flex items-center gap-2">
          <span className="font-semibold">總計：</span>
          <span className="px-2 py-1 bg-muted rounded-md font-medium">
            {totalMale + totalFemale} 隻
          </span>
        </div>
      </CardFooter>
    </Card>
  );
};

export default CustomerCountChart;
