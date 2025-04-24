import React, { useState } from "react";
import { TaskFormData, TaskFilter } from "@/pages/Todoist/types";
import TaskForm from "./TaskForm";
import TaskList from "./TaskList";
import {
  useQueryTasks,
  useAddTaskMutation,
  TasksQueryParams,
} from "./hooks/useTaskQueries";
import { useTodoistSettingsStore } from "./hooks/useTodoistSettingStore";
import TodoistSettings from "./TodoistSettings";
import { BatchAggregate } from "@/types";

interface TaskListProps {
  batch?: BatchAggregate;
}

/**
 * Todoist 主任務管理頁面組件
 * - 提供批次任務的查詢、建立、過濾與設定
 * - 結合 Todoist API 與本地設定，支援批次標籤與專案切換
 */
const Todoist: React.FC<TaskListProps> = ({ batch }) => {
  // 取得批次名稱，若無 batch 則為 null
  // Why: 讓所有任務操作都能明確關聯到批次，便於批次管理
  const batchName = batch?.index.batch_name || null;

  // 從全域 store 取得預設專案ID，確保所有操作都在同一專案下
  const {
    settings: { defaultProjectId },
  } = useTodoistSettingsStore();

  // 控制任務過濾條件（已完成/全部、排序）
  // Why: 讓使用者可自訂檢視條件，提升 UX
  const [filter, setFilter] = useState<TaskFilter>({
    showCompleted: !!batchName,
    order: "desc",
  });

  // 查詢任務的預設參數，根據 batchName 動態調整
  // Why: 查詢條件集中管理，避免重複傳遞與易於維護
  const INITIAL_PARAMS: TasksQueryParams = batch
    ? {
        project_id: defaultProjectId,
        label: batchName,
        getCompleted: filter.showCompleted,
      }
    : {
        project_id: defaultProjectId,
        getCompleted: filter.showCompleted,
      };

  // 控制新增任務表單顯示
  // Why: 僅允許單一表單同時顯示，避免 UI 混亂
  const [isAddingTask, setIsAddingTask] = useState(false);

  // 任務表單狀態，預設帶入 batchName 與專案ID
  // Why: 新增任務時自動帶入批次標籤，減少手動輸入
  const [formData, setFormData] = useState<TaskFormData>({
    content: "",
    description: "",
    due_string: "",
    due_lang: "TW",
    priority: 1,
    labels: [batchName ?? ""],
    project_id: defaultProjectId,
  });

  // 查詢任務清單，根據 filter 與 batch 動態取得資料
  // Why: 保持資料與 UI 狀態同步
  const { data: tasks, isLoading, error } = useQueryTasks(INITIAL_PARAMS);
  // 建立任務 mutation hook，確保查詢與新增一致性
  const addTaskMutation = useAddTaskMutation(INITIAL_PARAMS);

  // 處理表單欄位變更事件
  // Why: 動態更新 formData 狀態，支援所有欄位
  const handleInputChange = (
    e: React.ChangeEvent<
      HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
    >
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: name === "priority" ? parseInt(value, 10) : value,
    }));
  };

  // 提交任務表單事件
  // Why: 驗證內容後才送出，成功後重置表單並關閉
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.content.trim()) {
      addTaskMutation.mutate(formData, {
        onSuccess: () => {
          // 重置表單內容與狀態
          setFormData({
            content: "",
            description: "",
            due_string: "",
            due_lang: "TW",
            priority: 1,
            labels: [batchName ?? ""],
            project_id: defaultProjectId,
          });
          setIsAddingTask(false);
        },
      });
    }
  };

  // 切換顯示已完成任務的狀態
  // Why: 讓使用者可自由切換任務清單顯示範圍
  const toggleShowCompleted = () => {
    setFilter((prev) => ({
      ...prev,
      showCompleted: !prev.showCompleted,
    }));
  };

  // 若尚未設定預設專案，導向設定頁，避免查詢失敗
  if (!defaultProjectId) {
    return <TodoistSettings />;
  }

  // UI 主體區塊：控制列、新增表單、任務清單
  // Why: 分區明確，維護性高，易於擴充
  return (
    <div className="p-4 bg-white rounded-lg">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold">批次相關任務</h2>
        <div className="flex items-center gap-2">
          {/* 排序切換，方便用戶自訂檢視順序 */}
          <button
            onClick={() =>
              setFilter((prev) => ({
                ...prev,
                order: prev.order === "asc" ? "desc" : "asc",
              }))
            }
            className={`px-3 py-1 border rounded-md text-sm transition-colors ${
              filter.order === "asc"
                ? "bg-green-50 border-green-200 text-green-700"
                : "bg-gray-50 border-gray-200 text-gray-700"
            }`}
            title={filter.order === "asc" ? "到期日由舊到新" : "到期日由新到舊"}
          >
            {filter.order === "asc" ? "到期日↑" : "到期日↓"}
          </button>
          {/* 切換顯示已完成/全部任務 */}
          <button
            onClick={toggleShowCompleted}
            className={`px-3 py-1 border rounded-md text-sm transition-colors ${
              filter.showCompleted
                ? "bg-blue-50 border-blue-200 text-blue-700"
                : "bg-gray-50 border-gray-200 text-gray-700"
            }`}
          >
            {filter.showCompleted ? "顯示全部" : "顯示已完成"}
          </button>
          {/* 只有 batchName 存在才允許新增任務 */}
          {batchName && (
            <button
              onClick={() => setIsAddingTask(!isAddingTask)}
              className="px-3 py-1 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors text-sm"
            >
              {isAddingTask ? "取消" : "新增任務"}
            </button>
          )}
        </div>
      </div>

      {/* 新增任務表單區塊，僅在 isAddingTask 時顯示 */}
      {isAddingTask && batchName && (
        <TaskForm
          batchName={batchName}
          formData={formData}
          onChange={handleInputChange}
          onSubmit={handleSubmit}
          onCancel={() => setIsAddingTask(false)}
          isSubmitting={addTaskMutation.isPending}
          isError={addTaskMutation.isError}
          error={addTaskMutation.error}
        />
      )}

      {/* 顯示活動任務清單，根據 filter 決定顯示內容 */}
      <TaskList
        tasks={tasks}
        params={INITIAL_PARAMS}
        isLoading={isLoading}
        error={error}
        filter={filter}
        batch={batch}
      />
    </div>
  );
};

export default Todoist;
