import React from "react";
import { Task, TaskFilter } from "./types";
import TaskItem from "./TaskItem";
import { TasksQueryParams } from "./hooks/useTaskQueries";
import { BatchAggregate } from "@/types";

/**
 * TaskListProps
 * @description 任務清單元件的屬性型別，明確定義資料來源與狀態
 */
interface TaskListProps {
  tasks: Task[];
  params: TasksQueryParams;
  isLoading: boolean;
  error: Error | null;
  filter: TaskFilter;
  batch?: BatchAggregate;
}

/**
 * TaskList
 * @description 顯示批次任務清單，根據 loading/error 狀態與過濾器切換內容
 * - 使用 React.memo 優化單一任務渲染效能
 * - 支援 loading/error/empty 狀態分支
 */
const TaskList: React.FC<TaskListProps> = ({
  tasks,
  params,
  isLoading,
  error,
  filter,
  batch,
}) => {
  /**
   * 使用 React.memo 包裝 TaskItem
   * - 只在 id 或完成狀態變更時才重新渲染
   * - 避免父層渲染導致所有子任務重繪，提高效能
   */
  const MemoTaskItem = React.memo(TaskItem, (prevProps, nextProps) => {
    return (
      prevProps.task.id === nextProps.task.id &&
      prevProps.task.is_completed === nextProps.task.is_completed
    );
  });
  // 資料載入中時顯示 loading 狀態，避免用戶誤會無資料
  if (isLoading) {
    return (
      <div className="py-8 text-center">
        <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-blue-500 border-t-transparent"></div>
        <p className="mt-2 text-gray-500">載入中...</p>
      </div>
    );
  }

  // 載入失敗時顯示錯誤訊息，提升用戶信心與錯誤追蹤
  if (error) {
    return (
      <div className="py-6 text-center text-red-500">
        <p>錯誤: {error.message}</p>
        <p className="text-sm mt-1">請稍後再試或聯繫系統管理員</p>
      </div>
    );
  }

  // 無任務時顯示提示，鼓勵用戶建立新任務
  if (tasks.length === 0) {
    return (
      <div className="py-6 text-center text-gray-500">
        <p>暫無未完成任務</p>
        <p className="text-sm mt-1">
          點擊上方「新增任務」按鈕添加批次相關的待辦事項
        </p>
      </div>
    );
  }

  /**
   * 主清單渲染區塊
   * - 根據 filter 決定是否顯示已完成任務
   * - 每個任務都用 MemoTaskItem 包裝，避免不必要重渲染
   */
  return (
    <div className="divide-y divide-gray-100">
      {tasks
        .filter((task) => filter.showCompleted || !task.is_completed)
        .sort(
          filter.order === "asc"
            ? (a, b) =>
                new Date(a.due?.date ?? "").getTime() -
                new Date(b.due?.date ?? "").getTime()
            : (a, b) =>
                new Date(b.due?.date ?? "").getTime() -
                new Date(a.due?.date ?? "").getTime()
        )
        .map((task) => (
          <MemoTaskItem
            key={task.id}
            task={task}
            params={params}
            batch={batch}
          />
        ))}
    </div>
  );
};

export default TaskList;
