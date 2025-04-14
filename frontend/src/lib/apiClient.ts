import useGeneralSettingsStore from "@/pages/SettingsPage/hooks/useGeneralSettingsStore";
import axios from "axios";

const {
  settings: { apiUrl },
} = useGeneralSettingsStore.getState();

export const API_URL = new URL(apiUrl);

export const createApiClient = () => {
  const {
    settings: { apiUrl },
  } = useGeneralSettingsStore.getState();
  return axios.create({
    baseURL: apiUrl.origin,
    headers: {
      "Content-Type": "application/json",
    },
  });
};
