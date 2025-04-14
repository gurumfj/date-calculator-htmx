import { TasksQueryParams } from "@/pages/Todoist/hooks/useTaskQueries";
import { Project, Task, TaskFormData } from "@/pages/Todoist/types";
import { createApiClient } from "@/lib/apiClient";
import { AxiosError } from "axios";

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
interface ApiErrorResponse {
  message?: string;
  [key: string]: any;
}

const apiClient = createApiClient();

export const todoistApi = {
  getProjects: async (): Promise<Project[]> => {
    const response = await apiClient
      .get("/api/todoist/projects")
      .catch(handleApiError);
    return response.data;
  },
  getTasks: async (params: TasksQueryParams): Promise<Task[]> => {
    const response = await apiClient
      .get("/api/todoist/tasks", {
        params,
      })
      .catch(handleApiError);
    return response.data;
  },
  getCompletedTasks: async (params: TasksQueryParams): Promise<Task[]> => {
    const response = await apiClient
      .get("/api/todoist/completed", {
        params,
      })
      .catch(handleApiError);
    return response.data;
  },
  createTask: async (taskData: TaskFormData): Promise<Task> => {
    const response = await apiClient
      .post("/api/todoist/create_task", taskData)
      .catch(handleApiError);
    return response.data;
  },
  closeTask: async (taskId: string): Promise<Task> => {
    const response = await apiClient
      .post(`/api/todoist/close_task/${taskId}`)
      .catch(handleApiError);
    return response.data;
  },
  reopenTask: async (taskId: string): Promise<Task> => {
    const response = await apiClient
      .post(`/api/todoist/reopen_task/${taskId}`)
      .catch(handleApiError);
    return response.data;
  },
  deleteTask: async (taskId: string): Promise<Task> => {
    const response = await apiClient
      .post(`/api/todoist/delete_task/${taskId}`)
      .catch(handleApiError);
    return response.data;
  },
};

export default todoistApi;
