import React from "react";
import { cn } from "@/lib/utils";

/**
 * 自定義資訊卡屬性介面
 */
export interface CustomInfoCardProps {
  /** 圖示元件 */
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  /** 卡片標題 */
  title: string;
  /** 卡片內容 */
  children: React.ReactNode;
  /** 額外的CSS類別 */
  className?: string;
  /** 點擊卡片時的回調函數 */
  onClick?: () => void;
}

/**
 * 自定義資訊卡元件
 * 
 * 用於顯示批次的資訊項目，包含圖示、標題和內容
 */
export const CustomInfoCard: React.FC<CustomInfoCardProps> = ({
  icon: Icon,
  title,
  children,
  className = "",
  onClick,
}) => {
  return (
    <div 
      className={cn(
        "flex items-center space-x-3",
        onClick && "cursor-pointer",
        className
      )}
      onClick={onClick}
    >
      <div className="w-8 h-8 flex items-center justify-center rounded-full bg-[#F2F2F7]">
        <Icon className="w-4 h-4 text-[#8E8E93]" />
      </div>
      <div>
        <div className="text-xs text-[#8E8E93]">{title}</div>
        <div className="text-sm font-medium text-[#1C1C1E]">{children}</div>
      </div>
    </div>
  );
};

export default CustomInfoCard;
