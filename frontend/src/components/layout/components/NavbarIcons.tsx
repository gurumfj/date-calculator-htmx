import React from "react";
import NavbarAction from "./NavbarAction";
import {
  ArrowLeftIcon,
  PlusIcon,
  PencilIcon,
  TrashIcon,
  DocumentArrowDownIcon,
  MagnifyingGlassIcon,
  Cog6ToothIcon,
  ChartBarIcon
} from "@heroicons/react/24/outline";

/**
 * 圖標操作按鈕 - 純圖標版本
 */
interface IconActionProps {
  icon: React.ReactNode;
  onClick?: () => void;
  title?: string;
  className?: string;
}

export const IconAction: React.FC<IconActionProps> = ({
  icon,
  onClick,
  title,
  className = ""
}) => (
  <NavbarAction
    icon={icon}
    onClick={onClick}
    iconOnly={true}
    title={title}
    className={className}
  />
);

/**
 * 返回按鈕 - 使用 HeroIcons
 */
export const BackAction: React.FC<{ onClick?: () => void; title?: string }> = ({
  onClick,
  title = "返回"
}) => (
  <IconAction
    icon={<ArrowLeftIcon className="w-5 h-5" />}
    onClick={onClick}
    title={title}
  />
);

/**
 * 添加按鈕 - 使用 HeroIcons
 */
export const AddAction: React.FC<{ onClick?: () => void; title?: string }> = ({
  onClick,
  title = "新增"
}) => (
  <IconAction
    icon={<PlusIcon className="w-5 h-5" />}
    onClick={onClick}
    title={title}
    className="text-blue-500"
  />
);

/**
 * 編輯按鈕 - 使用 HeroIcons
 */
export const EditAction: React.FC<{ onClick?: () => void; title?: string }> = ({
  onClick,
  title = "編輯"
}) => (
  <IconAction
    icon={<PencilIcon className="w-5 h-5" />}
    onClick={onClick}
    title={title}
  />
);

/**
 * 刪除按鈕 - 使用 HeroIcons
 */
export const DeleteAction: React.FC<{ onClick?: () => void; title?: string }> = ({
  onClick,
  title = "刪除"
}) => (
  <IconAction
    icon={<TrashIcon className="w-5 h-5" />}
    onClick={onClick}
    title={title}
    className="text-red-500"
  />
);

/**
 * 保存按鈕 - 使用 HeroIcons
 */
export const SaveAction: React.FC<{ onClick?: () => void; title?: string }> = ({
  onClick,
  title = "保存"
}) => (
  <IconAction
    icon={<DocumentArrowDownIcon className="w-5 h-5" />}
    onClick={onClick}
    title={title}
  />
);

/**
 * 搜索按鈕 - 使用 HeroIcons
 */
export const SearchAction: React.FC<{ onClick?: () => void; title?: string }> = ({
  onClick,
  title = "搜索"
}) => (
  <IconAction
    icon={<MagnifyingGlassIcon className="w-5 h-5" />}
    onClick={onClick}
    title={title}
  />
);

/**
 * 設置按鈕 - 使用 HeroIcons
 */
export const SettingsAction: React.FC<{ onClick?: () => void; title?: string }> = ({
  onClick,
  title = "設置"
}) => (
  <IconAction
    icon={<Cog6ToothIcon className="w-5 h-5" />}
    onClick={onClick}
    title={title}
  />
);

/**
 * 圖表按鈕 - 使用 HeroIcons
 */
export const ChartAction: React.FC<{ onClick?: () => void; title?: string }> = ({
  onClick,
  title = "圖表"
}) => (
  <IconAction
    icon={<ChartBarIcon className="w-5 h-5" />}
    onClick={onClick}
    title={title}
  />
);
