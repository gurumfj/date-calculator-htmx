import React from "react";

// LoadingSpinner 元件屬性類型
interface LoadingSpinnerProps {
  show: boolean;
  children: React.ReactNode;
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ show, children }) => {
  if (!show) return <>{children}</>;

  return (
    <div>
      <div>{children}</div>
      <div>
        <div></div>
      </div>
    </div>
  );
};

export default LoadingSpinner;
