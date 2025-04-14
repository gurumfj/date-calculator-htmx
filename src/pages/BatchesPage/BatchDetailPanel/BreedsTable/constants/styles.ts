/**
 * BatchDetail 元件樣式常數
 * 提供統一的色彩和樣式定義
 */

export const COLORS = {
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
  STATUS: {
    SUCCESS: {
      BACKGROUND: "bg-green-100",
      TEXT: "text-green-700",
    },
    WARNING: {
      BACKGROUND: "bg-yellow-100",
      TEXT: "text-yellow-800",
    },
    INFO: {
      BACKGROUND: "bg-blue-100",
      TEXT: "text-blue-700",
    },
    DEFAULT: {
      BACKGROUND: "bg-gray-100",
      TEXT: "text-gray-700",
    },
  },
};

export const TYPOGRAPHY = {
  HEADER: {
    SM: "text-sm font-medium",
    MD: "text-lg font-medium",
    LG: "text-xl font-semibold",
  },
  BODY: {
    XS: "text-xs",
    SM: "text-sm",
  },
};

export const SPACING = {
  PADDING: {
    CARD: "p-4",
    TABLE_CELL: "px-4 py-2",
  },
  MARGIN: {
    SM: "space-y-3",
    MD: "space-y-4",
    LG: "space-y-6",
  },
  GAP: {
    SM: "gap-3",
    MD: "gap-4",
  },
};

export const LAYOUT = {
  ROUNDED: "rounded-xl",
  ROUNDED_SM: "rounded-lg",
  SHADOW: "shadow-sm",
};

export const TABLE = {
  HEADER: `${TYPOGRAPHY.BODY.XS} font-medium text-[${COLORS.TEXT.SECONDARY}] tracking-wider`,
  CELL: `${TYPOGRAPHY.BODY.SM} text-[${COLORS.TEXT.PRIMARY}]`,
  HEADER_BG: `bg-[${COLORS.BACKGROUND.LIGHT}]`,
  ROW_HOVER: `hover:bg-[${COLORS.BACKGROUND.LIGHT}]`,
  BORDER: `divide-y divide-[${COLORS.BORDER.LIGHT}]`,
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
