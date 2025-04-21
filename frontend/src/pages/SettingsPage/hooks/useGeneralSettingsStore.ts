import { create } from "zustand";
import { persist } from "zustand/middleware";
import axios from "axios";

export const getBackendUrl = () => {
  // 生產環境 Backend proxy
  const getCurrentProtocol = () => {
    return window.location.protocol;
  };
  const getCurrentHost = () => {
    return window.location.host;
  };
  const result = new URL(`${getCurrentProtocol()}//${getCurrentHost()}`);
  return result;
};

interface GeneralSettings {
  apiUrl: string;
}

interface GeneralSettingsStore {
  settings: GeneralSettings;
  saveSettings: (settings: GeneralSettings) => void;
  testConnection: (apiUrl: URL) => Promise<boolean>;
}

export const defaultGeneralSettings: GeneralSettings = {
  apiUrl: import.meta.env.VITE_API_URL || `${getBackendUrl()}`,
};

export const useGeneralSettingsStore = create<GeneralSettingsStore>()(
  persist(
    (set) => ({
      settings: defaultGeneralSettings,
      saveSettings: (settings: GeneralSettings) => set({ settings }),
      testConnection: async (apiUrl: URL) => {
        try {
          const res = await axios.get(`${apiUrl.origin}/api/health`, {
            timeout: 5000,
          });
          return res.data.status === "healthy";
        } catch (error) {
          console.error("API連線測試失敗:", error);
          return false;
        }
      },
    }),
    {
      name: "general-settings",
      partialize: (state) => ({
        settings: state.settings,
      }),
    }
  )
);

export default useGeneralSettingsStore;
