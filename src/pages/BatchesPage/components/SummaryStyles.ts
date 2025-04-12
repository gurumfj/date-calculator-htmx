/**
 * 摘要卡片樣式常數
 * 提供統一的色彩和樣式定義，供 BatchDetail、SalesDetail 和 FeedsDetail 使用
 */

export const SUMMARY_STYLES = {
  COLORS: {
    TEXT: {
      PRIMARY: "#1C1C1E",
      SECONDARY: "#8E8E93",
    },
    BACKGROUND: {
      WHITE: "#FFFFFF",
      LIGHT: "#F2F2F7",
    },
    BORDER: {
      LIGHT: "#F2F2F7",
    },
  },
  CONTAINER: "bg-white rounded-xl p-4 space-y-4",
  GRID: "grid grid-cols-2 md:grid-cols-2 lg:grid-cols-4 gap-4",
  ICON_CONTAINER: "bg-white rounded-xl p-2",
  TITLE: "text-xs text-[#8E8E93]",
  CONTENT: "text-sm font-medium text-[#1C1C1E]",
  CARD: "flex items-center space-x-3",
};

// 共用狀態樣式
export const STATUS_STYLES = {
  LOADING: {
    CONTAINER: "bg-white rounded-xl p-4 text-center",
    TEXT: "text-sm text-[#8E8E93]",
  },
  ERROR: {
    CONTAINER: "bg-white rounded-xl p-4 text-center",
    TEXT: "text-sm text-red-500",
  },
  EMPTY: {
    CONTAINER: "bg-white rounded-xl p-4 text-center",
    TEXT: "text-sm text-[#8E8E93]",
  },
};
