import ReactMarkdown from "react-markdown";
import remarkBreaks from "remark-breaks";
import React from "react";
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
import { useNavigate } from "react-router-dom";
import { BatchAggregate } from "@/types";
import { calculateDayAge, calculateWeekAge } from "@/utils/dateUtils";

interface TaskItemProps {
  task: Task;
  params: TasksQueryParams;
  batch?: BatchAggregate;
}

const TaskItem: React.FC<TaskItemProps> = ({ task, params, batch }) => {
  // 依據 batch 產生雞齡資訊，若無 batch 則 weekAge 為 null
  // Why: 讓批次管理與任務截止日期能連動顯示雞齡，方便農場管理決策
  const weekAge = batch?.breeds[0].breed_date
    ? calculateWeekAge(
        calculateDayAge(
          batch.breeds[0].breed_date,
          new Date(task.due?.date || "")
        )
      )
    : null;

  // 綁定三種 mutation hooks，分別處理完成、重開、刪除任務
  // Why: 明確分離不同操作，提升可維護性與可測試性
  const {
    mutate: onComplete,
    isPending: isCompletePending,
    isSuccess: isCompleteSuccess,
  } = useCompleteTaskMutation(params);
  const {
    mutate: onReopen,
    isPending: isReopenPending,
    isSuccess: isReopenSuccess,
  } = useReopenTaskMutation(params);
  const {
    mutate: onDelete,
    isPending: isDeletePending,
    isSuccess: isDeleteSuccess,
  } = useDeleteTaskMutation(params);

  // 處理任務狀態切換（完成/重開）
  // Why: 用單一 handler 管理狀態切換，避免重複邏輯
  const handleTaskToggle = () => {
    // 若已完成則重開，否則標記為完成
    if (task.is_completed) {
      onReopen(task.id);
    } else {
      onComplete(task.id);
    }
  };

  const navigate = useNavigate();

  // 點擊標籤時導向對應批次頁面
  // Why: 提升批次與任務之間的可追溯性
  const handleLabelClick = (label: string) => {
    navigate(`/batches/${label}`);
  };

  // 刪除任務前二次確認，避免誤刪
  // Why: 保護資料安全，符合使用者直覺
  const handleTaskDelete = () => {
    if (window.confirm("確定要刪除這個任務嗎？")) {
      onDelete(task.id);
    }
  };

  // 編輯任務時，優先嘗試打開 app，失敗則 fallback 到 web
  // Why: 提供跨裝置最佳體驗，兼容桌面與行動端
  const handleTaskEdit = () => {
    const webUrl = `https://todoist.com/app/task/${task.id}`;
    const appUrl = `todoist://task?id=${task.id}`;
    const iframe = document.createElement("iframe");
    iframe.style.display = "none";
    document.body.appendChild(iframe);
    setTimeout(() => {
      window.open(webUrl, "_blank");
      document.body.removeChild(iframe);
    }, 500);
    iframe.src = appUrl;
  };

  // 異步操作進行中或剛完成時，顯示 loading 狀態，避免重複操作
  // Why: 提升 UX，避免多次觸發 API
  if (
    isCompletePending ||
    isReopenPending ||
    isDeletePending ||
    isCompleteSuccess ||
    isReopenSuccess ||
    isDeleteSuccess
  ) {
    return (
      <div className="py-3 flex items-start group opacity-50">
        <div className="h-4 w-4 mt-1 mr-3"></div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between">
            <div className="flex items-center flex-wrap mr-2">
              <p className="font-medium text-gray-400">
                {task.content} <span className="animate-pulse">處理中...</span>
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // 主內容區：任務資訊、標籤、優先級、操作按鈕
  // Why: 分區明確，便於維護與擴充
  const priorityDisplay = getPriorityDisplay(task.priority);

  return (
    <div className="py-3 flex items-start group">
      {/* 狀態勾選框，切換完成/未完成 */}
      <input
        type="checkbox"
        checked={task.is_completed || false}
        onChange={handleTaskToggle}
        className="mt-1 mr-3 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
      />
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center flex-wrap mr-2">
            {/* 任務主標題，完成時顯示刪除線 */}
            <p
              className={`font-medium ${task.is_completed ? "line-through text-gray-400" : "text-gray-900"}`}
            >
              {task.content}
            </p>
            {/* 顯示優先級標誌，僅 priority > 1 才顯示 */}
            {task.priority > 1 && (
              <span
                className={`ml-2 px-2 py-0.5 text-xs rounded-full ${priorityDisplay.bgColor} ${priorityDisplay.textColor}`}
              >
                {priorityDisplay.label}
              </span>
            )}
            {/* 顯示批次標籤，可點擊導向批次頁 */}
            {Array.isArray(task.labels) && task.labels.length > 0 &&
              task.labels.map((label) => (
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
          {/* 操作按鈕群組：編輯與刪除，僅 hover 時顯示 */}
          <div className="flex space-x-2 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              onClick={handleTaskEdit}
              className="text-gray-400 hover:text-blue-500"
              aria-label="在 Todoist 中編輯任務"
              title="在 Todoist 中編輯"
            >
              <PencilIcon className="h-4 w-4" />
            </button>
            <button
              onClick={handleTaskDelete}
              className="text-gray-400 hover:text-red-500"
              aria-label="刪除任務"
              title="刪除任務"
            >
              <TrashIcon className="h-4 w-4" />
            </button>
          </div>
        </div>
        {/* 任務描述，支援 markdown，已完成時顯示灰色 */}
        {task.description && (
          <div
            className={`prose prose-sm max-w-none text-sm mt-1 ${task.is_completed ? "text-gray-400" : "text-gray-500"}`}
          >
            <ReactMarkdown remarkPlugins={[remarkBreaks]}>
              {task.description}
            </ReactMarkdown>
          </div>
        )}
        {/* 截止日期與雞齡資訊，若有提供 batch 才顯示雞齡 */}
        {task.due && (
          <p
            className={`text-xs mt-1 flex items-center ${task.is_completed ? "text-gray-400" : "text-gray-500"}`}
          >
            <CalendarIcon className="h-3 w-3 mr-1" />
            截止日期: {task.due.date}
            {weekAge ? ` (${weekAge.week}週 ${weekAge.day}天)` : ""}
          </p>
        )}
      </div>
    </div>
  );
};

export default TaskItem;
