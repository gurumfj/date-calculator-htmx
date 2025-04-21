import useGeneralSettingsStore from "@/pages/SettingsPage/hooks/useGeneralSettingsStore";
import axios from "axios";

const {
  settings: { apiUrl },
} = useGeneralSettingsStore.getState();

export const API_URL = new URL(apiUrl);

export const createApiClient = () => {
  const { settings } = useGeneralSettingsStore.getState();
  if (!settings.apiUrl) {
    throw new Error("API URL is not set");
  }
  return axios.create({
    baseURL: new URL(settings.apiUrl).origin,
    headers: {
      "Content-Type": "application/json",
    },
  });
};
