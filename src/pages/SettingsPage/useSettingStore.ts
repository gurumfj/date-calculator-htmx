import { create } from "zustand";
import { persist } from "zustand/middleware";
import { SystemSettings, GeneralSettings, BatchSettings } from "./types";
// import { supabase } from "@utils/supabaseClient";

// 默認設定值
const defaultSettings: SystemSettings = {
  general: {
    farmName: "",
    enableNotifications: false,
    darkMode: false,
    language: "zh-TW",
    apiUrl: "",
  },
  batch: {
    defaultChickenBreed: "BLACK_FEATHER",
    autoGenerateBatchNames: true,
    batchNameFormat: "YYYYMMDD-BREED",
    defaultFarmLocation: "主場",
    autoCompleteAfterSale: true,
  },
};

// 創建 Zustand Store
interface SettingsState {
  settings: SystemSettings;
  isLoading: boolean;
  error: Error | null;

  // 設定操作方法
  setGeneralSettings: (settings: GeneralSettings) => void;
  setBatchSettings: (settings: BatchSettings) => void;

  // 持久化到 Supabase
  saveSettings: () => Promise<void>;

  // 初始化加載設定
  fetchSettings: () => Promise<void>;
}

// 創建並導出設定 Store
export const useSettingsStore = create<SettingsState>()(
  persist(
    (set, get) => ({
      settings: defaultSettings,
      isLoading: false,
      error: null,

      // 更新設定方法
      setGeneralSettings: (generalSettings) =>
        set((state) => ({
          settings: { ...state.settings, general: generalSettings },
        })),

      setBatchSettings: (batchSettings) =>
        set((state) => ({
          settings: { ...state.settings, batch: batchSettings },
        })),

      // 保存所有設定到本地存儲
      saveSettings: async () => {
        set({ isLoading: true, error: null });
        try {
          const { settings } = get();

          // 實際情況可能需要保存到後端或其他持久化存儲
          // 但目前我們使用 localStorage 作為臨時解決方案
          localStorage.setItem("cleansales-settings", JSON.stringify(settings));

          // 模擬一個短暫的延遲
          await new Promise((resolve) => setTimeout(resolve, 300));

          set({ isLoading: false });
          return Promise.resolve();
        } catch (error) {
          set({
            isLoading: false,
            error: error instanceof Error ? error : new Error("Unknown error"),
          });
          return Promise.reject(error);
        }
      },

      // 從 Supabase 獲取設定
      fetchSettings: async () => {
        set({ isLoading: true, error: null });
        try {
          // 模擬從 API 獲取設定
          // const { data, error } = await supabase
          //   .from('user_settings')
          //   .select('*')
          //   .single();

          // 為演示目的使用 setTimeout 模擬 API 請求延遲
          await new Promise((resolve) => setTimeout(resolve, 500));

          // 假設我們有一些保存的設定
          const mockData = {
            general: {
              farmName: "陽光養雞場",
              enableNotifications: true,
              darkMode: true,
              language: "zh-TW",
              apiUrl: "https://api.example.com",
            },
            batch: {
              defaultChickenBreed: "BLACK_FEATHER",
              autoGenerateBatchNames: true,
              batchNameFormat: "YYYYMMDD-BREED",
              defaultFarmLocation: "主場",
              autoCompleteAfterSale: true,
            },
          };

          set({
            settings: mockData as SystemSettings,
            isLoading: false,
          });

          return Promise.resolve();
        } catch (error) {
          set({
            isLoading: false,
            error: error instanceof Error ? error : new Error("Unknown error"),
          });
          return Promise.reject(error);
        }
      },
    }),
    {
      name: "cleansales-settings", // localStorage 中的 key 名稱
      // 不保存 loading 和 error 狀態
      partialize: (state) => ({
        settings: state.settings,
      }),
    }
  )
);

// 使用設定的 Hook
export function useSettings() {
  const {
    settings,
    isLoading,
    error,
    setGeneralSettings,
    setBatchSettings,
    saveSettings,
    fetchSettings,
  } = useSettingsStore();

  return {
    settings,
    isLoading,
    error,
    setGeneralSettings,
    setBatchSettings,
    saveSettings,
    fetchSettings,
  };
}
