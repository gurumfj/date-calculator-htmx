import React, { useMemo } from "react";
import { formatDate } from "@utils/dateUtils";
import { calculateDayAge, calculateWeekAge } from "@utils/dateUtils";
import { sortBreedsByAge } from "@utils/batchCalculations";
import { BreedRecordRow } from "@app-types";
import CommonTable, { ColumnType } from "@components/common/CommonTable";

export interface ChickenDataTableProps {
  batch: {
    breeds: BreedRecordRow[];
  };
  isLoading?: boolean;
  error?: Error | null;
}

export const BreedsRecordsTable: React.FC<ChickenDataTableProps> = ({
  batch,
  isLoading = false,
  error = null,
}) => {
  const sortedBreeds = useMemo(
    () => sortBreedsByAge(batch.breeds),
    [batch.breeds]
  );

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl p-4 text-center">
        <div className="text-sm text-[#8E8E93]">載入中...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-xl p-4 text-center">
        <div className="text-sm text-red-500">
          載入資料時發生錯誤: {error.message}
        </div>
      </div>
    );
  }

  if (!batch.breeds || batch.breeds.length === 0) {
    return (
      <div className="bg-white rounded-xl p-4 text-center">
        <div className="text-sm text-[#8E8E93]">無入雛資料</div>
      </div>
    );
  }

  // 定義列
  const columns: ColumnType[] = [
    {
      key: "breed_date",
      title: "入雛日",
      render: (value) => formatDate(value),
    },
    {
      key: "supplier",
      title: "種母場",
      render: (value) => value || "-",
    },
    {
      key: "dayAge",
      title: "日齡",
      render: (_, record) => calculateDayAge(record.breed_date, new Date()),
    },
    {
      key: "weekAge",
      title: "週齡",
      render: (_, record) => {
        const dayAge = calculateDayAge(record.breed_date, new Date());
        const weekAge = calculateWeekAge(dayAge);
        return `${weekAge.week}.${weekAge.day}`;
      },
    },
    {
      key: "breed_male",
      title: "公雞數量",
    },
    {
      key: "breed_female",
      title: "母雞數量",
    },
  ];

  // 移動端卡片渲染函數 - 更新為與SalesTable相同的風格
  const renderMobileCard = (record: BreedRecordRow, index: number) => {
    const dayAge = calculateDayAge(record.breed_date, new Date());
    const weekAge = calculateWeekAge(dayAge);

    return (
      <div
        key={record.unique_id || index}
        className="bg-white p-3 rounded-xl shadow-sm"
      >
        <div className="flex justify-between items-start mb-2">
          <div>
            <div className="text-sm font-medium">
              {record.supplier || "未記錄種母場"}
            </div>
            <div className="text-xs text-gray-500">
              {formatDate(record.breed_date)}
            </div>
          </div>
          <div className="text-right">
            <div className="text-xs text-gray-500">日齡</div>
            <div className="text-sm">{dayAge}</div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-500">週齡:</span>
            <span>
              {weekAge.week}.{weekAge.day}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">公雞:</span>
            <span>{record.breed_male || 0} 隻</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">母雞:</span>
            <span>{record.breed_female || 0} 隻</span>
          </div>
          {record.chicken_breed && (
            <div className="flex justify-between">
              <span className="text-gray-500">品種:</span>
              <span>{record.chicken_breed}</span>
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <CommonTable
      title="入雛記錄"
      columns={columns}
      data={sortedBreeds}
      renderMobileCard={renderMobileCard}
      emptyText="無入雛資料"
    />
  );
};
