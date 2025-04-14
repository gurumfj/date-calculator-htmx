import React from "react";
import { Task, TaskFilter } from "./types";
import TaskItem from "./TaskItem";
import { TasksQueryParams } from "./hooks/useTaskQueries";

interface TaskListProps {
  tasks: Task[];
  params: TasksQueryParams;
  isLoading: boolean;
  error: Error | null;
  filter: TaskFilter;
}

const TaskList: React.FC<TaskListProps> = ({
  tasks,
  params,
  isLoading,
  error,
  filter,
}) => {
  // ?為什麼要使用memo, 用法是什麼？
  const MemoTaskItem = React.memo(TaskItem, (prevProps, nextProps) => {
    return (
      prevProps.task.id === nextProps.task.id &&
      prevProps.task.is_completed === nextProps.task.is_completed
    );
  });
  if (isLoading) {
    return (
      <div className="py-8 text-center">
        <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-blue-500 border-t-transparent"></div>
        <p className="mt-2 text-gray-500">載入中...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="py-6 text-center text-red-500">
        <p>錯誤: {error.message}</p>
        <p className="text-sm mt-1">請稍後再試或聯繫系統管理員</p>
      </div>
    );
  }

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

  return (
    <div className="divide-y divide-gray-100">
      {tasks
        .filter((task) => filter.showCompleted || !task.is_completed)
        .map((task) => (
          <MemoTaskItem key={task.id} task={task} params={params} />
        ))}
    </div>
  );
};

export default TaskList;
