import React from "react";
import { ChickenBreedType, CHICKEN_BREEDS } from "@app-types"; // Use types from src/types

type SortOrder = "asc" | "desc";

interface BatchFiltersProps {
  selectedBreed: ChickenBreedType | null;
  isCompleted: boolean;
  sortOrder: SortOrder;
  handleBreedChange: (breed: ChickenBreedType) => void;
  toggleIsCompleted: () => void;
  toggleSortOrder: () => void;
}

export const BatchFilters: React.FC<BatchFiltersProps> = ({
  selectedBreed,
  isCompleted,
  sortOrder,
  handleBreedChange,
  toggleIsCompleted,
  toggleSortOrder,
}) => (
  <div className="mb-6 flex flex-wrap items-center gap-2">
    {/* 雞種過濾按鈕 */}
    {CHICKEN_BREEDS.map((breed) => (
      <button
        key={breed}
        onClick={() => handleBreedChange(breed)}
        className={`
          rounded-md px-4 py-2 text-sm font-medium transition-colors
          focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
          ${
            selectedBreed === breed
              ? "bg-blue-600 text-white shadow-sm hover:bg-blue-700"
              : "bg-gray-100 text-gray-700 hover:bg-gray-200"
          }
        `}
      >
        {breed}
      </button>
    ))}
    {/* 完成狀態切換按鈕 */}
    <button
      onClick={toggleIsCompleted}
      className={`
        ml-auto rounded-md px-4 py-2 text-sm font-medium transition-colors
        focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2
        ${
          isCompleted
            ? "bg-green-600 text-white shadow-sm hover:bg-green-700"
            : "bg-gray-100 text-gray-700 hover:bg-gray-200"
        }
      `}
    >
      {isCompleted ? "顯示未完成" : "顯示已完成"}
    </button>
    {/* 排序順序切換按鈕 */}
    <button
      onClick={toggleSortOrder}
      className={`
        ml-2 rounded-md px-4 py-2 text-sm font-medium transition-colors
        focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2
        bg-purple-100 text-purple-700 hover:bg-purple-200
      `}
    >
      排序: {sortOrder === "asc" ? "日期舊到新" : "日期新到舊"}
    </button>
  </div>
);
