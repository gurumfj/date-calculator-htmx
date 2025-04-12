import React from "react";
import { useNavigate } from "react-router-dom";
import NavbarAction from "./NavbarAction";
import { ArrowLeftIcon } from "@heroicons/react/24/outline";

interface BackButtonProps {
  to?: string;
  onClick?: () => void;
  label?: string;
  className?: string;
  iconOnly?: boolean;
  title?: string;
}

/**
 * 返回按鈕元件 - 可配置為純圖標或帶文字
 */
const BackButton: React.FC<BackButtonProps> = ({
  to,
  onClick,
  label = "返回",
  className = "",
  iconOnly = false,
  title,
}) => {
  const navigate = useNavigate();

  const handleClick = () => {
    if (onClick) {
      onClick();
    } else if (to) {
      navigate(to);
    } else {
      navigate(-1); // 默認返回上一頁
    }
  };

  return (
    <NavbarAction
      onClick={handleClick}
      icon={<ArrowLeftIcon className="h-5 w-5" />}
      label={iconOnly ? undefined : label}
      iconOnly={iconOnly}
      title={title || label} // 如果沒有提供 title，則使用 label
      className={className}
    />
  );
};

export default BackButton;