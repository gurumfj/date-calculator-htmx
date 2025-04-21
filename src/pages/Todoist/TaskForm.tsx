import React from "react";
import {
  CalendarIcon,
  FlagIcon,
  ExclamationCircleIcon,
} from "@heroicons/react/24/outline";
import { TaskFormData, priorityOptions } from "./types";

interface TaskFormProps {
  batchName: string;
  formData: TaskFormData;
  onChange: (
    e: React.ChangeEvent<
      HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
    >
  ) => void;
  onSubmit: (e: React.FormEvent) => void;
  onCancel: () => void;
  isSubmitting: boolean;
  isError: boolean;
  error: Error | null;
}

const TaskForm: React.FC<TaskFormProps> = ({
  batchName,
  formData,
  onChange,
  onSubmit,
  onCancel,
  isSubmitting,
  isError,
  error,
}) => {
  // 提取錯誤信息
  const errorMessage = error?.message || "提交任務時發生錯誤，請稍後再試";

  return (
    <form
      onSubmit={onSubmit}
      className="mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200"
    >
      {/* 錯誤提示區域 */}
      {isError && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
          <div className="flex items-start">
            <ExclamationCircleIcon className="h-5 w-5 text-red-500 mt-0.5 mr-2 flex-shrink-0" />
            <div className="text-sm text-red-600">{errorMessage}</div>
          </div>
        </div>
      )}

      <div className="mb-3">
        <label
          htmlFor="content"
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          任務內容 <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          id="content"
          name="content"
          value={formData.content}
          onChange={onChange}
          required
          className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 ${
            isError
              ? "border-red-300 focus:ring-red-500"
              : "border-gray-300 focus:ring-blue-500"
          }`}
          placeholder="輸入任務內容"
          autoComplete="off"
        />
      </div>

      <div className="mb-3">
        <label
          htmlFor="description"
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          任務描述
        </label>
        <textarea
          id="description"
          name="description"
          value={formData.description}
          onChange={onChange}
          rows={2}
          className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 ${
            isError
              ? "border-red-300 focus:ring-red-500"
              : "border-gray-300 focus:ring-blue-500"
          }`}
          placeholder="輸入任務描述（選填）"
        />
        <div className="text-xs text-gray-500 mt-1">
          此任務將自動關聯到批次：{batchName}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 mb-4">
        <div>
          <label
            htmlFor="due_string"
            className="block text-sm font-medium text-gray-700 mb-1 flex items-center"
          >
            <CalendarIcon className="w-4 h-4 mr-1" />
            截止日期
          </label>
          <input
            type="text"
            id="due_string"
            name="due_string"
            value={formData.due_string}
            onChange={onChange}
            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 ${
              isError
                ? "border-red-300 focus:ring-red-500"
                : "border-gray-300 focus:ring-blue-500"
            }`}
            placeholder="例如：今天, 明天, 下週一"
            autoComplete="off"
          />
        </div>

        <div>
          <label
            htmlFor="priority"
            className="block text-sm font-medium text-gray-700 mb-1 flex items-center"
          >
            <FlagIcon className="w-4 h-4 mr-1" />
            優先級
          </label>
          <select
            id="priority"
            name="priority"
            value={formData.priority}
            onChange={onChange}
            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 ${
              isError
                ? "border-red-300 focus:ring-red-500"
                : "border-gray-300 focus:ring-blue-500"
            }`}
          >
            {priorityOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="flex justify-end">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 mr-3 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-100"
          disabled={isSubmitting}
        >
          取消
        </button>
        <button
          type="submit"
          className={`px-4 py-2 text-white rounded-md ${
            isSubmitting
              ? "bg-blue-300"
              : isError
                ? "bg-red-500 hover:bg-red-600"
                : "bg-blue-500 hover:bg-blue-600"
          }`}
          disabled={isSubmitting || !formData.content.trim()}
        >
          {isSubmitting ? "添加中..." : "添加任務"}
        </button>
      </div>
    </form>
  );
};

export default TaskForm;
