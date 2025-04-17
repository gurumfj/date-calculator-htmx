import React, { ReactNode } from "react";
import { SUMMARY_STYLES } from "./SummaryStyles";
import { Card, CardContent } from "@/components/ui/card";

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

/**
 * 通用摘要卡片組件
 * 用於在不同頁面中展示批次相關的摘要資訊
 */
const SummaryCard: React.FC<SummaryCardProps> = ({ items, className = "" }) => {
  const renderInfoCard = (
    { icon: IconComponent, title, content, className = "" }: SummaryCardItem,
    index: number
  ) => (
    <div key={index} className={`${SUMMARY_STYLES.CARD} ${className}`}>
      <div className={SUMMARY_STYLES.ICON_CONTAINER}>
        <IconComponent className="w-4 h-4 text-[#8E8E93]" />
      </div>
      <div>
        <div className={SUMMARY_STYLES.TITLE}>{title}</div>
        <div className={SUMMARY_STYLES.CONTENT}>{content}</div>
      </div>
    </div>
  );

  return (
    <Card className={className}>
      <CardContent className="p-4">
        <div className={SUMMARY_STYLES.GRID}>
          {items.map((item, index) => renderInfoCard(item, index))}
        </div>
      </CardContent>
    </Card>
  );
};

export default SummaryCard;
