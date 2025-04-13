import axios, { AxiosError } from "axios";
import { getBackendUrl } from "./supabaseClient";
import { TasksQueryParams } from "src/pages/BatchesPage/BatchDetailPanel/todoist/hooks";
import {
  Task,
  TaskFormData,
} from "src/pages/BatchesPage/BatchDetailPanel/todoist/types";

// API 基礎路徑
const API_BASE_URL = import.meta.env.VITE_API_URL || `${getBackendUrl()}`;

interface ApiErrorResponse {
  message?: string;
  [key: string]: any;
}

// 創建一個處理錯誤的通用函數
const handleApiError = (error: AxiosError<ApiErrorResponse>) => {
  if (!error.response) {
    throw new Error("網絡連接失敗，請檢查您的網絡！");
  }

  const errorMessage = error.response?.data?.message || "";

  switch (error.response.status) {
    case 500:
      throw new Error(`伺服器錯誤！${errorMessage}`);
    case 400:
      throw new Error(`請求參數錯誤！${errorMessage}`);
    case 401:
      throw new Error(`身份驗證失敗，請重新登入！`);
    // 更多狀態碼...
    default:
      throw new Error(`請求失敗(${error.response.status})：${errorMessage}`);
  }
};

export const todoistApi = {
  getTasks: async (params: TasksQueryParams): Promise<Task[]> => {
    const response = await axios
      .get(`${API_BASE_URL}/api/todoist/tasks`, {
        params,
      })
      .catch(handleApiError);
    return response.data;
  },
  getCompletedTasks: async (params: TasksQueryParams): Promise<Task[]> => {
    const response = await axios
      .get(`${API_BASE_URL}/api/todoist/completed`, {
        params,
      })
      .catch(handleApiError);
    return response.data;
  },
  createTask: async (taskData: TaskFormData): Promise<Task> => {
    const response = await axios
      .post(`${API_BASE_URL}/api/todoist/create_task`, taskData)
      .catch(handleApiError);
    return response.data;
  },
  closeTask: async (taskId: string): Promise<Task> => {
    const response = await axios
      .post(`${API_BASE_URL}/api/todoist/close_task/${taskId}`)
      .catch(handleApiError);
    return response.data;
  },
  reopenTask: async (taskId: string): Promise<Task> => {
    const response = await axios
      .post(`${API_BASE_URL}/api/todoist/reopen_task/${taskId}`)
      .catch(handleApiError);
    return response.data;
  },
  deleteTask: async (taskId: string): Promise<Task> => {
    const response = await axios
      .post(`${API_BASE_URL}/api/todoist/delete_task/${taskId}`)
      .catch(handleApiError);
    return response.data;
  },
};

export default API_BASE_URL;
