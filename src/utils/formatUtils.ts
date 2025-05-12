/**
 * 格式化工具函數
 * Why: 統一應用程式中的數據格式化邏輯，確保一致的用戶體驗
 */

/**
 * 格式化重量數據
 * @param value 重量值
 * @returns 格式化後的重量字串，包含單位(斤)
 */
export const formatWeight = (value: number | null | undefined): string => {
  if (value === null || value === undefined) return "-";
  return `${value.toLocaleString()} 斤`;
};

/**
 * 格式化貨幣數據
 * @param value 貨幣值
 * @returns 格式化後的貨幣字串，包含貨幣符號
 */
export const formatCurrency = (value: number | null | undefined): string => {
  if (value === null || value === undefined) return "-";
  return `$${value.toLocaleString()}`;
};
