import React from "react";

// InfoCard 元件屬性類型
interface InfoCardProps {
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  title: string;
  children: React.ReactNode;
  bgColor?: string;
  textColor?: string;
}

// InfoCard 元件：用於顯示詳細資訊，可自定義圖標、標題和內容
const InfoCard: React.FC<InfoCardProps> = ({
  icon: Icon,
  title,
  children,
  bgColor = "bg-blue-50",
  textColor = "text-blue-500",
}) => {
  return (
    <div>
      <div
        className={`flex items-center justify-center w-7 h-7 rounded-full ${bgColor} mr-3`}
      >
        <Icon className={`${textColor} text-sm`} />
      </div>
      <div>
        <div>{title}</div>
        <div>{children}</div>
      </div>
    </div>
  );
};

export default InfoCard;
