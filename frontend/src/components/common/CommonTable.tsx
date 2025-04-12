import React, { useState, ReactNode } from "react";

// 通用的顏色常數
export const TABLE_COLORS = {
  TEXT: {
    PRIMARY: "#1C1C1E",
    SECONDARY: "#8E8E93",
  },
  BACKGROUND: {
    WHITE: "#FFFFFF",
    LIGHT: "#F2F2F7",
    HOVER: "#F2F2F7",
  },
  BORDER: {
    LIGHT: "#F2F2F7",
  },
};

// 通用表格樣式
export const TABLE_STYLES = {
  CONTAINER: "bg-white rounded-xl overflow-hidden",
  HEADER: "p-4 border-b border-[#F2F2F7]",
  HEADER_TITLE: "text-lg font-medium text-[#1C1C1E]",
  TABLE: "min-w-full divide-y divide-[#F2F2F7]",
  THEAD: "bg-[#F2F2F7]",
  TH: "px-4 py-2 text-left text-xs font-medium text-[#8E8E93] tracking-wider",
  TH_RIGHT: "px-4 py-2 text-right text-xs font-medium text-[#8E8E93] tracking-wider",
  TBODY: "bg-white divide-y divide-[#F2F2F7]",
  TR: "hover:bg-[#F2F2F7]",
  TD: "px-4 py-2 text-sm text-[#1C1C1E]",
  TD_RIGHT: "px-4 py-2 text-sm text-[#1C1C1E] text-right",
  FOOTER: "p-4 border-t border-[#F2F2F7]",
  MOBILE_CARD: "bg-white p-3 rounded-xl shadow-sm",
  MOBILE_CARD_CONTAINER: "md:hidden space-y-2",
};

// 通用分頁樣式
export const PAGINATION_STYLES = {
  CONTAINER: "p-4 border-t border-[#F2F2F7]",
  BUTTON_ACTIVE: "px-4 py-2 text-sm font-medium rounded-lg bg-white text-[#007AFF] border border-[#007AFF] hover:bg-[#007AFF] hover:text-white transition-colors",
  BUTTON_DISABLED: "px-4 py-2 text-sm font-medium rounded-lg bg-[#F2F2F7] text-[#8E8E93] cursor-not-allowed",
  TEXT: "text-sm text-[#8E8E93]",
  MOBILE: {
    CONTAINER: "md:hidden flex justify-center space-x-2",
    BUTTON_ACTIVE: "w-10 h-10 flex items-center justify-center rounded-full bg-white text-[#007AFF] border border-[#007AFF]",
    BUTTON_DISABLED: "w-10 h-10 flex items-center justify-center rounded-full bg-[#F2F2F7] text-[#8E8E93] cursor-not-allowed",
    TEXT: "h-10 flex items-center justify-center text-sm text-[#8E8E93] px-3",
  },
  DESKTOP: {
    CONTAINER: "hidden md:flex items-center justify-between",
  },
};

// 通用格式化函數
export const formatDate = (dateString: string | undefined): string => {
  try {
    return dateString ? dateString.split("T")[0] : "-";
  } catch (error) {
    console.error("日期格式處理錯誤:", error);
    return "-";
  }
};

// 通用表格組件
export interface ColumnType {
  key: string;
  title: string;
  align?: 'left' | 'right' | 'center';
  render?: (value: any, record: any) => ReactNode;
}

export interface CommonTableProps {
  title: string;
  columns: ColumnType[];
  data: any[];
  itemsPerPage?: number;
  emptyText?: string;
  renderMobileCard?: (item: any, index: number) => ReactNode;
  renderFooter?: () => ReactNode;
}

export const CommonTable: React.FC<CommonTableProps> = ({
  title,
  columns,
  data,
  itemsPerPage = 10,
  emptyText = "無資料",
  renderMobileCard,
  renderFooter,
}) => {
  const [currentPage, setCurrentPage] = useState<number>(1);

  if (!data || !Array.isArray(data) || data.length === 0) {
    return (
      <div className={TABLE_STYLES.CONTAINER}>
        <div className={TABLE_STYLES.HEADER}>
          <h3 className={TABLE_STYLES.HEADER_TITLE}>{title}</h3>
        </div>
        <div className="p-4 text-center text-sm text-[#8E8E93]">{emptyText}</div>
      </div>
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

  return (
    <div className={TABLE_STYLES.CONTAINER}>
      <div className={TABLE_STYLES.HEADER}>
        <h3 className={TABLE_STYLES.HEADER_TITLE}>{title}</h3>
      </div>

      {/* 移動端卡片式佈局 */}
      {renderMobileCard && (
        <div className={TABLE_STYLES.MOBILE_CARD_CONTAINER}>
          {currentData.map((item, index) => renderMobileCard(item, index))}
        </div>
      )}

      {/* 桌面端表格式佈局 */}
      <div className={renderMobileCard ? "overflow-x-auto hidden md:block" : "overflow-x-auto"}>
        <table className={TABLE_STYLES.TABLE}>
          <thead className={TABLE_STYLES.THEAD}>
            <tr>
              {columns.map((column, index) => (
                <th
                  key={index}
                  className={
                    column.align === 'right'
                      ? TABLE_STYLES.TH_RIGHT
                      : column.align === 'center'
                        ? TABLE_STYLES.TH.replace('text-left', 'text-center')
                        : TABLE_STYLES.TH
                  }
                >
                  {column.title}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className={TABLE_STYLES.TBODY}>
            {currentData.map((record, rowIndex) => (
              <tr key={rowIndex} className={TABLE_STYLES.TR}>
                {columns.map((column, colIndex) => (
                  <td
                    key={colIndex}
                    className={
                      column.align === 'right'
                        ? TABLE_STYLES.TD_RIGHT
                        : column.align === 'center'
                          ? TABLE_STYLES.TD.replace('text-left', 'text-center')
                          : TABLE_STYLES.TD
                    }
                  >
                    {column.render
                      ? column.render(record[column.key], record)
                      : record[column.key] || '-'}
                  </td>
                ))}
              </tr>
            ))}
            {renderFooter && renderFooter()}
          </tbody>
        </table>
      </div>

      {/* 分頁控制 */}
      {totalPages > 1 && (
        <div className={PAGINATION_STYLES.CONTAINER}>
          {/* 移動端分頁 - 簡潔版 */}
          <div className={PAGINATION_STYLES.MOBILE.CONTAINER}>
            <button
              onClick={() => handlePageChange(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
              className={currentPage === 1
                ? PAGINATION_STYLES.MOBILE.BUTTON_DISABLED
                : PAGINATION_STYLES.MOBILE.BUTTON_ACTIVE}
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-5 w-5"
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
            </button>
            <div className={PAGINATION_STYLES.MOBILE.TEXT}>
              {currentPage} / {totalPages}
            </div>
            <button
              onClick={() => handlePageChange(Math.min(totalPages, currentPage + 1))}
              disabled={currentPage === totalPages}
              className={currentPage === totalPages
                ? PAGINATION_STYLES.MOBILE.BUTTON_DISABLED
                : PAGINATION_STYLES.MOBILE.BUTTON_ACTIVE}
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-5 w-5"
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
            </button>
          </div>

          {/* 桌面端分頁 - 完整版 */}
          <div className={PAGINATION_STYLES.DESKTOP.CONTAINER}>
            <button
              onClick={() => handlePageChange(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
              className={currentPage === 1
                ? PAGINATION_STYLES.BUTTON_DISABLED
                : PAGINATION_STYLES.BUTTON_ACTIVE}
            >
              上一頁
            </button>
            <span className={PAGINATION_STYLES.TEXT}>
              第 {currentPage} 頁 / 共 {totalPages} 頁
            </span>
            <button
              onClick={() => handlePageChange(Math.min(totalPages, currentPage + 1))}
              disabled={currentPage === totalPages}
              className={currentPage === totalPages
                ? PAGINATION_STYLES.BUTTON_DISABLED
                : PAGINATION_STYLES.BUTTON_ACTIVE}
            >
              下一頁
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default CommonTable;
