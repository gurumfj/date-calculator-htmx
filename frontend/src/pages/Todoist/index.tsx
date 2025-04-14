import React, { useState } from "react";
import { BatchAggregate } from "@app-types";
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

interface TodoistProps {
  batch: BatchAggregate | null;
}

const Todoist: React.FC<TodoistProps> = ({ batch }) => {
  // 狀態管理
  const {
    settings: { defaultProjectId },
  } = useTodoistSettingsStore();

  const INITIAL_PARAMS: TasksQueryParams = batch
    ? {
        project_id: defaultProjectId,
        label: batch?.batchName ? batch.batchName : "",
      }
    : {
        project_id: defaultProjectId,
      };
  const [filter, setFilter] = useState<TaskFilter>({
    showCompleted: true,
  });
  const [isAddingTask, setIsAddingTask] = useState(false);
  const [formData, setFormData] = useState<TaskFormData>({
    content: "",
    description: "",
    due_string: "",
    due_lang: "TW",
    priority: 1,
    labels: [batch?.batchName ?? ""],
    project_id: defaultProjectId,
  });

  // 查詢活動任務和已完成項目
  const { data: tasks, isLoading, error } = useTaskQueries(INITIAL_PARAMS);

  // Mutation hooks
  const addTaskMutation = useAddTaskMutation(INITIAL_PARAMS);

  // 事件處理函數
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

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.content.trim()) {
      addTaskMutation.mutate(formData, {
        onSuccess: () => {
          // 重置表單
          setFormData({
            content: "",
            description: "",
            due_string: "",
            due_lang: "TW",
            priority: 1,
            labels: [batch?.batchName ?? ""],
            project_id: defaultProjectId,
          });
          setIsAddingTask(false);
        },
      });
    }
  };

  const toggleShowCompleted = () => {
    setFilter((prev) => ({
      ...prev,
      showCompleted: !prev.showCompleted,
    }));
  };

  if (!defaultProjectId) {
    return <TodoistSettings />;
  }

  return (
    <div className="p-4 bg-white rounded-lg">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold">批次相關任務</h2>
        <div className="flex items-center gap-2">
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
          {batch && (
            <button
              onClick={() => setIsAddingTask(!isAddingTask)}
              className="px-3 py-1 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors text-sm"
            >
              {isAddingTask ? "取消" : "新增任務"}
            </button>
          )}
        </div>
      </div>

      {isAddingTask && batch && (
        <TaskForm
          batch={batch}
          formData={formData}
          onChange={handleInputChange}
          onSubmit={handleSubmit}
          onCancel={() => setIsAddingTask(false)}
          isSubmitting={addTaskMutation.isPending}
          isError={addTaskMutation.isError}
          error={addTaskMutation.error}
        />
      )}

      {/* 顯示活動任務 */}
      <TaskList
        tasks={tasks}
        params={INITIAL_PARAMS}
        isLoading={isLoading}
        error={error}
        filter={filter}
      />
    </div>
  );
};

export default Todoist;
