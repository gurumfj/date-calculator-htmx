import { useMutation, useQueryClient, useQueries } from "@tanstack/react-query";
import { Task, TaskFormData } from "../types";
import { todoistApi } from "@app-lib/todoistApis";

export interface TasksQueryParams {
  project_id: string | null;
  label?: string | null;
}

export const useTaskQueries = (
  params: TasksQueryParams
): {
  data: Task[];
  isLoading: boolean;
  isError: boolean;
  error: Error | null;
} => {
  const results = useQueries({
    queries: [
      {
        queryKey: ["active_tasks", params],
        queryFn: async () => {
          try {
            // 使用標籤查詢批次相關的活動任務
            const response: Task[] = await todoistApi.getTasks(params);
            return response;
          } catch (error) {
            console.error("Error fetching tasks:", error);
            throw error;
          }
        },
      },
      {
        queryKey: ["completed_items", params],
        queryFn: async () => {
          try {
            if (!params.project_id) {
              return [];
            }
            // 查詢與批次相關的已完成項目
            const response: Task[] = await todoistApi.getCompletedTasks(params);
            return response;
          } catch (error) {
            console.warn("Error fetching completed items:", error);
            return [];
          }
        },
      },
    ],
  });
  return {
    data: results.flatMap((result) => result.data || []),
    isLoading: results.some((result) => result.isLoading),
    isError: results.some((result) => result.error),
    error: results.find((result) => result.error)?.error || null,
  };
};

// 添加任務
export const useAddTaskMutation = (params: TasksQueryParams) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (taskData: TaskFormData) => {
      // 創建請求數據
      const response = await todoistApi.createTask(taskData);

      return response;
    },
    onSuccess: () => {
      // 重新獲取任務列表
      queryClient.invalidateQueries({ queryKey: ["active_tasks", params] });
    },
  });
};

// 完成任務
export const useCompleteTaskMutation = (params: TasksQueryParams) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (taskId: string) => {
      const response = await todoistApi.closeTask(taskId);

      return response;
    },
    onSuccess: () => {
      // 完成任務後，需要更新兩個查詢：活動任務和已完成項目
      queryClient.invalidateQueries({ queryKey: ["active_tasks", params] });
      queryClient.invalidateQueries({ queryKey: ["completed_items", params] });
    },
  });
};

// 重新開啟已完成任務
export const useReopenTaskMutation = (params: TasksQueryParams) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (taskId: string) => {
      const response = await todoistApi.reopenTask(taskId);

      return response;
    },
    onSuccess: () => {
      // 重新開啟後需要更新兩個查詢
      queryClient.invalidateQueries({ queryKey: ["completed_items", params] });
      queryClient.invalidateQueries({ queryKey: ["active_tasks", params] });
    },
  });
};

// 刪除任務
export const useDeleteTaskMutation = (params: TasksQueryParams) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (taskId: string) => {
      const response = await todoistApi.deleteTask(taskId);

      return response;
    },
    onSuccess: () => {
      // 刪除後更新所有相關查詢
      queryClient.invalidateQueries({ queryKey: ["active_tasks", params] });
      queryClient.invalidateQueries({
        queryKey: ["completed_items", params],
      });
    },
  });
};
