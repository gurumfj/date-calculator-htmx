import React, { useState, ReactNode } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import {
  Table,
  TableHeader,
  TableBody,
  TableFooter,
  TableHead,
  TableRow,
  TableCell,
} from "@/components/ui/table";

// 通用格式化函數
export const formatDate = (dateString: string | undefined): string => {
  try {
    return dateString ? dateString.split("T")[0] : "-";
  } catch (error) {
    console.error("日期格式處理錯誤:", error);
    return "-";
  }
};

// 欄位類型定義
export interface ColumnType {
  key: string;
  title: string;
  align?: 'left' | 'right' | 'center';
  render?: (value: any, record: any) => ReactNode;
  // 配置在移動端卡片中的顯示方式
  mobileOptions?: {
    // 是否在移動端卡片中顯示
    show?: boolean;
    // 在移動端卡片中的顯示名稱 (如果不提供，使用title)
    label?: string;
    // 在移動端卡片中的位置類型
    position?: 'header' | 'content' | 'footer' | 'status';
    // 在移動端卡片中的欄位寬度 (1=半寬, 2=全寬)
    span?: 1 | 2;
  };
}

// 移動端卡片選項接口
export interface MobileCardOptions {
  // 卡片標題欄位的鍵名
  titleField?: string;
  // 卡片副標題欄位的鍵名
  subtitleField?: string;
  // 卡片右上角日期/狀態欄位的鍵名
  statusField?: string;
  // 卡片右上角狀態標籤的描述性文本
  statusLabel?: string;
  // 卡片頁腳欄位的鍵名
  footerField?: string;
  // 卡片頁腳標籤的描述性文本
  footerLabel?: string;
}

// 通用表格組件屬性接口
export interface CommonTableProps {
  title: string;
  columns: ColumnType[];
  data: any[];
  itemsPerPage?: number;
  emptyText?: string;
  renderMobileCard?: (item: any, index: number) => ReactNode;
  mobileCardOptions?: MobileCardOptions;
  renderFooter?: () => ReactNode;
  className?: string;
}

export const CommonTable: React.FC<CommonTableProps> = ({
  title,
  columns,
  data,
  itemsPerPage = 10,
  emptyText = "無資料",
  renderMobileCard,
  mobileCardOptions,
  renderFooter,
  className,
}) => {
  const [currentPage, setCurrentPage] = useState<number>(1);

  if (!data || !Array.isArray(data) || data.length === 0) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
        </CardHeader>
        <CardContent className="text-center text-sm text-muted-foreground">
          {emptyText}
        </CardContent>
      </Card>
    );
  }

  const totalPages = Math.ceil(data.length / itemsPerPage);
  const currentData = data.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  const handlePageChange = (pageNumber: number) => {
    setCurrentPage(pageNumber);
  };

  // 預設移動端卡片渲染
  const defaultRenderMobileCard = (item: any, index: number) => {
    // 如果沒有提供任何移動端選項，則使用第一個欄位作為標題
    const options = mobileCardOptions || {
      titleField: columns[0].key,
      subtitleField: columns.length > 1 ? columns[1].key : undefined,
    };

    const { titleField, subtitleField, statusField, statusLabel, footerField, footerLabel } = options;

    // 過濾標記為在移動端顯示的欄位，或者沒有指定的欄位（預設顯示）
    const contentColumns = columns.filter(
      (col) => !col.mobileOptions || col.mobileOptions.show !== false
    );

    return (
      <Card key={index} className="mb-2">
        <CardContent className="p-3">
          {/* 卡片標題區域 */}
          <div className="flex justify-between items-start mb-2">
            <div>
              {titleField && (
                <div className="text-sm font-medium">{item[titleField]}</div>
              )}
              {subtitleField && (
                <div className="text-xs text-muted-foreground">
                  {item[subtitleField] || "-"}
                </div>
              )}
            </div>
            {statusField && (
              <div className="text-right">
                {statusLabel && (
                  <div className="text-xs text-muted-foreground">{statusLabel}</div>
                )}
                <div className="text-sm">
                  {columns.find((col) => col.key === statusField)?.render
                    ? columns.find((col) => col.key === statusField)?.render!(item[statusField], item)
                    : item[statusField] || "-"}
                </div>
              </div>
            )}
          </div>

          {/* 卡片內容區域 - 網格佈局 */}
          <div className="grid grid-cols-2 gap-2 text-sm">
            {contentColumns
              .filter(
                (col) =>
                  col.key !== titleField &&
                  col.key !== subtitleField &&
                  col.key !== statusField &&
                  col.key !== footerField
              )
              .map((col, colIdx) => {
                // 決定欄位是否跨越整行（寬度 = 2）
                const spanFull = col.mobileOptions?.span === 2;
                
                return (
                  <div
                    key={colIdx}
                    className={cn(
                      "flex justify-between",
                      spanFull ? "col-span-2" : ""
                    )}
                  >
                    <span className="text-muted-foreground">
                      {col.mobileOptions?.label || col.title}:
                    </span>
                    <span>
                      {col.render
                        ? col.render(item[col.key], item)
                        : item[col.key] || "-"}
                    </span>
                  </div>
                );
              })}
          </div>

          {/* 卡片頁腳區域 */}
          {footerField && (
            <div className="mt-2 pt-2 border-t border-border flex justify-between">
              <span className="text-muted-foreground text-sm">
                {footerLabel || columns.find((col) => col.key === footerField)?.title || "總計"}:
              </span>
              <span className="font-medium text-sm">
                {columns.find((col) => col.key === footerField)?.render
                  ? columns.find((col) => col.key === footerField)?.render!(item[footerField], item)
                  : item[footerField] || "-"}
              </span>
            </div>
          )}
        </CardContent>
      </Card>
    );
  };

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>

      {/* 移動端卡片式佈局 */}
      <div className="md:hidden px-4 space-y-2">
        {currentData.map((item, index) => 
          renderMobileCard 
            ? renderMobileCard(item, index) 
            : defaultRenderMobileCard(item, index)
        )}
      </div>

      {/* 桌面端表格式佈局 */}
      <div className="overflow-x-auto hidden md:block">
        <Table>
          <TableHeader>
            <TableRow>
              {columns.map((column, index) => (
                <TableHead
                  key={index}
                  className={cn(
                    column.align === 'right' ? "text-right" : 
                    column.align === 'center' ? "text-center" : ""
                  )}
                >
                  {column.title}
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {currentData.map((record, rowIndex) => (
              <TableRow key={rowIndex}>
                {columns.map((column, colIndex) => (
                  <TableCell
                    key={colIndex}
                    className={cn(
                      column.align === 'right' ? "text-right" : 
                      column.align === 'center' ? "text-center" : ""
                    )}
                  >
                    {column.render 
                      ? column.render(record[column.key], record)
                      : record[column.key] || '-'}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
          {renderFooter && (
            <TableFooter>
              {renderFooter()}
            </TableFooter>
          )}
        </Table>
      </div>

      {/* 分頁控制 */}
      {totalPages > 1 && (
        <>
          <Separator />
          <div className="p-4">
            {/* 移動端分頁 - 簡潔版 */}
            <div className="md:hidden flex justify-center space-x-2">
              <Button
                size="icon"
                variant="outline"
                onClick={() => handlePageChange(Math.max(1, currentPage - 1))}
                disabled={currentPage === 1}
                className="h-8 w-8"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-4 w-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 19l-7-7 7-7"
                  />
                </svg>
              </Button>
              <div className="flex items-center text-sm text-muted-foreground px-3">
                {currentPage} / {totalPages}
              </div>
              <Button
                size="icon"
                variant="outline"
                onClick={() => handlePageChange(Math.min(totalPages, currentPage + 1))}
                disabled={currentPage === totalPages}
                className="h-8 w-8"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-4 w-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 5l7 7-7 7"
                  />
                </svg>
              </Button>
            </div>

            {/* 桌面端分頁 - 完整版 */}
            <div className="hidden md:flex items-center justify-between">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handlePageChange(Math.max(1, currentPage - 1))}
                disabled={currentPage === 1}
              >
                上一頁
              </Button>
              <span className="text-sm text-muted-foreground">
                第 {currentPage} 頁 / 共 {totalPages} 頁
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handlePageChange(Math.min(totalPages, currentPage + 1))}
                disabled={currentPage === totalPages}
              >
                下一頁
              </Button>
            </div>
          </div>
        </>
      )}
    </Card>
  );
};

export default CommonTable;
