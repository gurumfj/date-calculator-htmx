/**
 * 共用摘要卡片元件
 * Why: 統一摘要卡片樣式與行為，減少重複程式碼，提升維護效率。
 */
import React, { ReactNode } from "react";

import { Card, CardContent } from "@/components/ui/card";

/**
 * 摘要卡片項目介面
 * Why: 定義摘要卡片項目的結構，方便後續擴展和維護。
 */
export interface SummaryCardItem {
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  title: string;
  content: ReactNode;
  className?: string;
}

interface SummaryCardProps {
  items: SummaryCardItem[];
  className?: string;
}

const InfoCard: React.FC<SummaryCardItem> = ({
  icon: IconComponent,
  title,
  content,
  className = "",
}) => {
  return (
    <div className={`flex flex-row items-center gap-3 ${className}`}>
      <div className="flex-shrink-0 mr-2">
        <IconComponent className="w-4 h-4 text-[#8E8E93]" />
      </div>
      <div className="flex flex-col">
        <div className="text-xs text-gray-500">{title}</div>
        <div className="text-base font-semibold text-gray-900">{content}</div>
      </div>
    </div>
  );
};

/**
 * 通用摘要卡片組件
 * 用於在不同頁面中展示批次相關的摘要資訊
 */
const SummaryCard: React.FC<SummaryCardProps> = ({ items, className = "" }) => {
  return (
    <Card className={className}>
      <CardContent className="p-4">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {items.map((item, index) => (
            <InfoCard key={index} {...item} />
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

export default SummaryCard;
