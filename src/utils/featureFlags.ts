/**
 * 功能開關系統
 * 
 * 這個模組用於管理應用程式中的功能開關（Feature Flags）。
 * 使用功能開關可以控制特定功能的開啟/關閉，而不需要更改代碼或重新部署。
 */

// 定義所有可用的功能開關
export const FEATURES = {
  // 在這裡添加新的功能開關
  EXAMPLE_FEATURE: 'example_feature',
  // 範例：新的 UI 設計
  NEW_UI_DESIGN: 'new_ui_design',
  // 範例：進階搜尋功能
  ADVANCED_SEARCH: 'advanced_search',
  // 深色模式
  DARK_MODE: 'dark_mode',
  // 增強型銷售圖表
  ENHANCED_SALES_CHART: 'enhanced_sales_chart',
  // 桌面佈局已成為核心功能，不再需要功能開關
};

/**
 * 環境變數中的功能開關配置
 * 這允許通過環境變數控制功能開關
 */
const getEnvFeatureFlags = (): Record<string, boolean> => {
  const flags: Record<string, boolean> = {};
  
  // 讀取所有以 VITE_FEATURE_ 開頭的環境變數
  Object.keys(import.meta.env).forEach(key => {
    if (key.startsWith('VITE_FEATURE_')) {
      const featureName = key.replace('VITE_FEATURE_', '').toLowerCase();
      flags[featureName] = import.meta.env[key] === 'true';
    }
  });
  
  return flags;
};

/**
 * 從 localStorage 讀取功能開關設置
 */
const getLocalStorageFeatureFlags = (): Record<string, boolean> => {
  const storedFlags = localStorage.getItem('featureFlags');
  if (!storedFlags) return {};
  
  try {
    return JSON.parse(storedFlags);
  } catch (error) {
    console.error('無法解析 localStorage 中的功能開關設置', error);
    return {};
  }
};

/**
 * 將功能開關設置儲存到 localStorage
 */
export const saveFeatureFlags = (flags: Record<string, boolean>): void => {
  localStorage.setItem('featureFlags', JSON.stringify(flags));
};

/**
 * 獲取所有功能開關設置
 * 優先級：localStorage > 環境變數 > 默認值
 */
export const getAllFeatureFlags = (): Record<string, boolean> => {
  const envFlags = getEnvFeatureFlags();
  const localStorageFlags = getLocalStorageFeatureFlags();
  
  // 合併所有來源的功能開關設置
  return { ...envFlags, ...localStorageFlags };
};

/**
 * 檢查特定功能是否啟用
 * @param featureName 功能名稱
 * @param defaultValue 默認值（如果沒有設置）
 * @returns 功能是否啟用
 */
export const isFeatureEnabled = (featureName: string, defaultValue = false): boolean => {
  const allFlags = getAllFeatureFlags();
  return featureName in allFlags ? allFlags[featureName] : defaultValue;
};

/**
 * 啟用特定功能
 * @param featureName 功能名稱
 */
export const enableFeature = (featureName: string): void => {
  const allFlags = getAllFeatureFlags();
  saveFeatureFlags({ ...allFlags, [featureName]: true });
};

/**
 * 禁用特定功能
 * @param featureName 功能名稱
 */
export const disableFeature = (featureName: string): void => {
  const allFlags = getAllFeatureFlags();
  saveFeatureFlags({ ...allFlags, [featureName]: false });
};

/**
 * 切換功能狀態
 * @param featureName 功能名稱
 */
export const toggleFeature = (featureName: string): void => {
  const allFlags = getAllFeatureFlags();
  const currentValue = isFeatureEnabled(featureName);
  saveFeatureFlags({ ...allFlags, [featureName]: !currentValue });
};
