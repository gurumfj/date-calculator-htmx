import React, { useState, useEffect } from "react";
import { Task, getPriorityDisplay } from "./types";
import {
  CalendarIcon,
  TrashIcon,
  PencilIcon,
} from "@heroicons/react/24/outline";
import {
  TasksQueryParams,
  useCompleteTaskMutation,
  useDeleteTaskMutation,
  useReopenTaskMutation,
} from "./hooks/useTaskQueries";

interface TaskItemProps {
  task: Task;
  params: TasksQueryParams;
}

const TaskItem: React.FC<TaskItemProps> = ({ task, params }) => {
  const [prevTask, setPrevTask] = useState<{
    task: Task | null;
    processing: boolean;
    operationType: "complete" | "reopen" | "delete" | null;
  }>({
    task: task,
    processing: false,
    operationType: null,
  });
  const { mutate: onComplete, isPending: isCompletePending } =
    useCompleteTaskMutation(params);
  const { mutate: onReopen, isPending: isReopenPending } =
    useReopenTaskMutation(params);
  const { mutate: onDelete, isPending: isDeletePending } =
    useDeleteTaskMutation(params);
  // 處理任務狀態切換
  const handleTaskToggle = () => {
    if (prevTask.processing) return; // 如果正在處理，則忽略

    if (task.is_completed) {
      setPrevTask({
        task: {
          ...task,
          is_completed: false,
        },
        processing: true,
        operationType: "reopen",
      });
      onReopen(task.id);
    } else {
      setPrevTask({
        task: {
          ...task,
          is_completed: true,
        },
        processing: true,
        operationType: "complete",
      });
      onComplete(task.id);
    }
  };

  const handleLabelClick = (label: string) => {
    if (prevTask.processing) return; // 如果正在處理，則忽略
    // link to /batches/:batchName
    window.location.href = `/batches/${label}`;
  };

  // 處理任務刪除
  const handleTaskDelete = () => {
    if (prevTask.processing) return; // 如果正在處理，則忽略

    if (window.confirm("確定要刪除這個任務嗎？")) {
      setPrevTask({
        task: null,
        processing: true,
        operationType: "delete",
      });
      onDelete(task.id);
    }
  };

  // 處理任務編輯 - 同時支援桌面瀏覽器和移動設備
  const handleTaskEdit = () => {
    if (prevTask.processing || !prevTask.task) return; // 如果正在處理，則忽略

    // 使用Todoist的Web URL (適用於所有設備)
    const webUrl = `https://todoist.com/app/task/${prevTask.task.id}`;

    // 嘗試使用URL scheme (只在移動設備上有效)
    const appUrl = `todoist://task?id=${prevTask.task.id}`;

    // 使用這種方法可以先嘗試打開應用，如果失敗則打開網頁版
    // 創建一個隱藏的iframe嘗試app URL scheme
    const iframe = document.createElement("iframe");
    iframe.style.display = "none";
    document.body.appendChild(iframe);

    // 設置超時，如果app沒有打開，則轉到web版本
    setTimeout(() => {
      window.open(webUrl, "_blank");
      document.body.removeChild(iframe);
    }, 500);

    // 嘗試打開app
    iframe.src = appUrl;
  };

  useEffect(() => {
    if (isCompletePending || isReopenPending || isDeletePending) return;
    const timeout = setTimeout(() => {
      setPrevTask((prev) => ({
        task: prev.task,
        processing: false,
        operationType: null,
      }));
    }, 10000);
    return () => clearTimeout(timeout);
  }, [isCompletePending, isReopenPending, isDeletePending]);

  // 如果有操作正在進行中或等待查詢更新，顯示loading狀態
  if (prevTask.processing || !prevTask.task) {
    return (
      <div className="py-3 flex items-start group opacity-50">
        <div className="h-4 w-4 mt-1 mr-3"></div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between">
            <div className="flex items-center flex-wrap mr-2">
              <p className="font-medium text-gray-400">
                {prevTask?.task?.content}{" "}
                <span className="animate-pulse">處理中...</span>
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="py-3 flex items-start group">
      <input
        type="checkbox"
        checked={prevTask.task.is_completed || false}
        onChange={handleTaskToggle}
        className="mt-1 mr-3 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
        disabled={prevTask.processing}
      />
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center flex-wrap mr-2">
            <p
              className={`font-medium ${prevTask.task.is_completed ? "line-through text-gray-400" : "text-gray-900"}`}
            >
              {prevTask.task.content}
            </p>
            {/* 顯示優先級標誌 */}
            {prevTask.task.priority > 1 && (
              <span
                className={`ml-2 px-2 py-0.5 text-xs rounded-full ${getPriorityDisplay(prevTask.task.priority).bgColor} ${getPriorityDisplay(prevTask.task.priority).textColor}`}
              >
                {getPriorityDisplay(prevTask.task.priority).label}
              </span>
            )}

            {/* 顯示標籤 */}
            {prevTask.task.labels &&
              prevTask.task.labels.length > 0 &&
              prevTask.task.labels.map((label) => (
                <span
                  key={label}
                  className="ml-2 px-2 py-0.5 text-xs rounded-full bg-blue-100 text-blue-700 cursor-pointer"
                  onClick={() => handleLabelClick(label)}
                  role="button"
                  tabIndex={0}
                  aria-label={`批次: ${label}`}
                >
                  {label}
                </span>
              ))}
          </div>
          <div className="flex space-x-2 opacity-0 group-hover:opacity-100 transition-opacity">
            {/* 編輯按鈕 */}
            <button
              onClick={handleTaskEdit}
              className="text-gray-400 hover:text-blue-500"
              aria-label="在 Todoist 中編輯任務"
              disabled={prevTask.processing}
              title="在 Todoist 中編輯"
            >
              <PencilIcon className="h-4 w-4" />
            </button>

            {/* 刪除按鈕 */}
            <button
              onClick={handleTaskDelete}
              className="text-gray-400 hover:text-red-500"
              aria-label="刪除任務"
              disabled={prevTask.processing}
              title="刪除任務"
            >
              <TrashIcon className="h-4 w-4" />
            </button>
          </div>
        </div>

        {prevTask.task.description && (
          <p
            className={`text-sm mt-1 ${prevTask.task.is_completed ? "text-gray-400" : "text-gray-500"}`}
          >
            {prevTask.task.description}
          </p>
        )}

        {prevTask.task.due && (
          <p
            className={`text-xs mt-1 flex items-center ${prevTask.task.is_completed ? "text-gray-400" : "text-gray-500"}`}
          >
            <CalendarIcon className="h-3 w-3 mr-1" />
            截止日期: {prevTask.task.due.date}
          </p>
        )}
      </div>
    </div>
  );
};

export default TaskItem;
