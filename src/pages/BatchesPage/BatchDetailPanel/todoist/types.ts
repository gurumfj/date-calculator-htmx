// Todoist API 類型定義
// 轉換自 Python Todoist API 庫

// 視圖樣式類型
export type ViewStyle = "list" | "board";

// Due 日期類型
export interface Due {
  date: string;
  is_recurring: boolean;
  string: string;
  datetime?: string | null;
  timezone?: string | null;
}

// Duration 時長類型
export interface Duration {
  amount: number;
  unit: string;
}
// 基礎任務類型 - 包含 Task 和 Item 的共同欄位
export interface BaseTaskItem {
  id: string;
  content: string;
  description: string;
  priority: number;
  project_id: string;
  section_id: string | null;
  parent_id: string | number | null;
  labels: string[] | null;
  sync_id?: string | null;
  due: Due | null;
}

// Todoist API Task 類型
export interface Task extends BaseTaskItem {
  assignee_id: string | null;
  assigner_id: string | null;
  comment_count: number;
  is_completed: boolean;
  created_at: string;
  creator_id: string;
  order: number;
  url: string;
  duration: Duration | null;
}

// Item 類型
export interface Item extends BaseTaskItem {
  user_id: string;
  child_order: number;
  collapsed: boolean;
  checked: boolean;
  is_deleted: boolean;
  added_at: string;
  day_order?: number | null;
  added_by_uid?: string | null;
  assigned_by_uid?: string | null;
  responsible_uid?: string | null;
  completed_at?: string | null;
}

// 任務與項目之間的映射函數
export const taskToItem = (task: Task): Item => {
  return {
    // 基本字段直接映射
    id: task.id,
    content: task.content,
    description: task.description,
    priority: task.priority,
    project_id: task.project_id,
    section_id: task.section_id,
    due: task.due,
    sync_id: task.sync_id,
    labels: task.labels || [],

    // 特殊映射字段
    parent_id: task.parent_id ? Number(task.parent_id) : null,
    checked: task.is_completed,

    // Item特有字段設置默認值
    user_id: task.creator_id,
    child_order: task.order,
    collapsed: false,
    is_deleted: false,
    added_at: task.created_at,
    day_order: null,
    added_by_uid: task.creator_id,
    assigned_by_uid: task.assigner_id,
    responsible_uid: task.assignee_id,
    completed_at: task.is_completed ? new Date().toISOString() : null,
  };
};

// 項目轉任務的映射函數
export const itemToTask = (item: Item): Task => {
  return {
    // 基本字段直接映射
    id: item.id,
    content: item.content,
    description: item.description,
    priority: item.priority,
    project_id: item.project_id,
    section_id: item.section_id,
    due: item.due,
    sync_id: item.sync_id,
    labels: item.labels,

    // 特殊映射字段
    parent_id: item.parent_id ? String(item.parent_id) : null,
    is_completed: item.checked,

    // Task 特有字段設置默認值
    assignee_id: null,
    assigner_id: null,
    comment_count: 0,
    created_at: item.added_at,
    creator_id: item.user_id || item.added_by_uid || "",
    order: item.child_order,
    url: "",
    duration: null,
  };
};

// Project 專案類型
export interface Project {
  color: string;
  comment_count: number;
  id: string;
  is_favorite: boolean;
  is_inbox_project: boolean | null;
  is_shared: boolean;
  is_team_inbox: boolean | null;
  can_assign_tasks?: boolean | null;
  name: string;
  order: number;
  parent_id: string | null;
  url: string;
  view_style: ViewStyle;
}

// Section 分區類型
export interface Section {
  id: string;
  name: string;
  order: number;
  project_id: string;
}

// Label 標籤類型
export interface Label {
  id: string;
  name: string;
  color: string;
  order: number;
  is_favorite: boolean;
}

// Attachment 附件類型
export interface Attachment {
  resource_type?: string | null;
  file_name?: string | null;
  file_size?: number | null;
  file_type?: string | null;
  file_url?: string | null;
  file_duration?: number | null;
  upload_state?: string | null;
  image?: string | null;
  image_width?: number | null;
  image_height?: number | null;
  url?: string | null;
  title?: string | null;
}

// Comment 評論類型
export interface Comment {
  attachment: Attachment | null;
  content: string;
  id: string;
  posted_at: string;
  project_id: string | null;
  task_id: string | null;
}

// Collaborator 協作者類型
export interface Collaborator {
  id: string;
  email: string;
  name: string;
}

// QuickAddResult 快速添加結果類型
export interface QuickAddResult {
  task: Task;
  resolved_project_name?: string | null;
  resolved_assignee_name?: string | null;
  resolved_label_names?: string[] | null;
  resolved_section_name?: string | null;
}

// ItemCompletedInfo 完成項目信息類型
export interface ItemCompletedInfo {
  item_id: string;
  completed_items: number;
}

// CompletedItems 已完成項目列表類型
export interface CompletedItems {
  items: Item[];
  total: number;
  completed_info: ItemCompletedInfo[];
  has_more: boolean;
  next_cursor?: string | null;
}

// 自定義類型用於前端業務邏輯
export interface TaskFormData {
  content: string;
  description: string;
  due_string: string;
  due_lang: string;
  priority: number;
  labels?: string[];
  project_id: string;
}

export interface TaskFilter {
  showCompleted: boolean;
}

// 任務優先級選項
export const priorityOptions = [
  { value: 1, label: "低", bgColor: "bg-gray-100", textColor: "text-gray-500" },
  { value: 2, label: "中", bgColor: "bg-blue-100", textColor: "text-blue-500" },
  {
    value: 3,
    label: "高",
    bgColor: "bg-orange-100",
    textColor: "text-orange-500",
  },
  { value: 4, label: "緊急", bgColor: "bg-red-100", textColor: "text-red-500" },
];

// 獲取優先級顯示樣式
export const getPriorityDisplay = (priority: number) => {
  const option =
    priorityOptions.find((opt) => opt.value === priority) || priorityOptions[0];
  return option;
};

// TODO: 轉移到 .env
export const PROJECT_ID = "2351892378";
