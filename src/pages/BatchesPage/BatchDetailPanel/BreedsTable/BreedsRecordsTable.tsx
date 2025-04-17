import React, { useMemo } from "react";
import { formatDate } from "@utils/dateUtils";
import { calculateDayAge, calculateWeekAge } from "@utils/dateUtils";
import { sortBreedsByAge } from "@utils/batchCalculations";
import { BreedRecordRow } from "@app-types";
import CommonTable, { ColumnType } from "@components/common/CommonTable";
import { Card, CardContent } from "@/components/ui/card";

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
      <Card>
        <CardContent className="p-4 text-center">
          <div className="text-sm text-muted-foreground">載入中...</div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="p-4 text-center">
          <div className="text-sm text-destructive">
            載入資料時發生錯誤: {error.message}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!batch.breeds || batch.breeds.length === 0) {
    return (
      <Card>
        <CardContent className="p-4 text-center">
          <div className="text-sm text-muted-foreground">無入雛資料</div>
        </CardContent>
      </Card>
    );
  }

  // 定義列
  const columns: ColumnType[] = [
    {
      key: "breed_date",
      title: "入雛日",
      render: (value) => formatDate(value),
      mobileOptions: {
        position: "header",
        show: true
      }
    },
    {
      key: "supplier",
      title: "種母場",
      render: (value) => value || "-",
      mobileOptions: {
        position: "header",
        show: true
      }
    },
    {
      key: "dayAge",
      title: "日齡",
      render: (_, record) => calculateDayAge(record.breed_date, new Date()),
      mobileOptions: {
        position: "status",
        show: true,
        label: "日齡"
      }
    },
    {
      key: "weekAge",
      title: "週齡",
      render: (_, record) => {
        const dayAge = calculateDayAge(record.breed_date, new Date());
        const weekAge = calculateWeekAge(dayAge);
        return `${weekAge.week}.${weekAge.day}`;
      },
      mobileOptions: {
        position: "content",
        show: true,
        label: "週齡"
      }
    },
    {
      key: "breed_male",
      title: "公雞數量",
      mobileOptions: {
        position: "content",
        show: true,
        label: "公雞"
      }
    },
    {
      key: "breed_female",
      title: "母雞數量",
      mobileOptions: {
        position: "content",
        show: true,
        label: "母雞"
      }
    },
    {
      key: "chicken_breed",
      title: "品種",
      mobileOptions: {
        position: "content",
        show: true,
        label: "品種"
      }
    }
  ];

  return (
    <CommonTable
      title="入雛記錄"
      columns={columns}
      data={sortedBreeds}
      emptyText="無入雛資料"
      mobileCardOptions={{
        titleField: "supplier",
        subtitleField: "breed_date",
        statusField: "dayAge",
        statusLabel: "日齡"
      }}
    />
  );
};
