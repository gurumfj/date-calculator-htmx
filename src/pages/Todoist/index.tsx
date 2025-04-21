import React, { useState } from "react";
import { TaskFormData, TaskFilter } from "@/pages/Todoist/types";
import TaskForm from "./TaskForm";
import TaskList from "./TaskList";
import {
  useTaskQueries,
  useAddTaskMutation,
  TasksQueryParams,
} from "./hooks/useTaskQueries";
import { useTodoistSettingsStore } from "./hooks/useTodoistSettingStore";
import TodoistSettings from "./TodoistSettings";
import { useParams } from "react-router-dom";

/**
 * Todoist 主任務管理頁面組件
 * - 提供批次任務的查詢、建立、過濾與設定
 * - 結合 Todoist API 與本地設定，支援批次標籤與專案切換
 * @returns {JSX.Element}
 */
const Todoist: React.FC = () => {
  // 取得路由參數，用於批次標籤過濾
  const { batchName } = useParams();

  // 狀態管理
  // 從全域 store 取得預設專案ID，確保所有操作都在同一專案下
  const {
    settings: { defaultProjectId },
  } = useTodoistSettingsStore();

  /**
   * 查詢任務的預設參數
   * - 若有 batchName 則帶入 label 過濾
   * - 保證查詢聚焦於當前專案與批次
   */
  const INITIAL_PARAMS: TasksQueryParams = batchName
    ? {
        project_id: defaultProjectId,
        label: batchName,
      }
    : {
        project_id: defaultProjectId,
      };
  // 控制「顯示已完成」的任務過濾器，預設批次頁面顯示全部
  const [filter, setFilter] = useState<TaskFilter>({
    showCompleted: batchName ? true : false,
  });
  /**
   * 控制任務排序狀態
   * - 預設為降冪（最近到期的在上）
   * - 由 UI 按鈕切換 asc/desc
   */
  const [order, setOrder] = useState<"asc" | "desc">("desc");
  // 控制新增任務表單顯示狀態，避免同時出現多個表單
  const [isAddingTask, setIsAddingTask] = useState(false);
  /**
   * 任務表單狀態
   * - 預設帶入 batchName 作為 labels
   * - 預設語言為 TW，priority 為 1
   */
  const [formData, setFormData] = useState<TaskFormData>({
    content: "",
    description: "",
    due_string: "",
    due_lang: "TW",
    priority: 1,
    labels: [batchName ?? ""],
    project_id: defaultProjectId,
  });

  // 查詢活動任務和已完成項目
  // 查詢任務清單，根據 INITIAL_PARAMS 動態取得資料
  const { data: tasks, isLoading, error } = useTaskQueries(INITIAL_PARAMS);

  // Mutation hooks
  // 建立任務的 mutation hook，確保與查詢參數一致
  const addTaskMutation = useAddTaskMutation(INITIAL_PARAMS);

  /**
   * 處理表單欄位變更事件
   * - 動態更新 formData 狀態
   * - 若欄位為 priority 則轉為數字型別
   * @param e - 來自 input/textarea/select 的變更事件
   */
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

  /**
   * 提交任務表單事件
   * - 驗證內容不為空後呼叫 addTaskMutation
   * - 成功後重置表單並關閉新增表單狀態
   * @param e - 表單提交事件
   */
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.content.trim()) {
      addTaskMutation.mutate(formData, {
        onSuccess: () => {
          // 重置表單，確保下次新增為空白狀態
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

  /**
   * 切換顯示已完成任務的狀態
   * - 讓使用者可自由切換任務清單顯示範圍
   */
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

  /**
   * UI 主體區塊
   * - 上方為控制列（切換顯示、開啟新增表單）
   * - 中間動態顯示 TaskForm
   * - 下方顯示 TaskList，根據查詢與過濾狀態呈現
   */
  return (
    <div className="p-4 bg-white rounded-lg">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold">批次相關任務</h2>
        <div className="flex items-center gap-2">
          {/* 排序切換按鈕，提供到期日升冪/降冪切換，方便用戶自訂檢視順序 */}
          <button
            onClick={() => setOrder((prev) => (prev === "asc" ? "desc" : "asc"))}
            className={`px-3 py-1 border rounded-md text-sm transition-colors ${
              order === "asc"
                ? "bg-green-50 border-green-200 text-green-700"
                : "bg-gray-50 border-gray-200 text-gray-700"
            }`}
            title={order === "asc" ? "到期日由舊到新" : "到期日由新到舊"}
          >
            {order === "asc" ? "到期日↑" : "到期日↓"}
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
        order={order}
      />
    </div>
  );
};

export default Todoist;
