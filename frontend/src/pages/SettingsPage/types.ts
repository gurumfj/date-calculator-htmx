// src/types/settings.ts

// 一般系統設定介面
export interface GeneralSettings {
  farmName: string;
  enableNotifications: boolean;
  darkMode: boolean;
  language: string;
  apiUrl: string;
}

// 批次設定介面
export interface BatchSettings {
  defaultChickenBreed: string;
  autoGenerateBatchNames: boolean;
  batchNameFormat: string;
  defaultFarmLocation: string;
  autoCompleteAfterSale: boolean;
}

// Todoist 設定介面
export interface TodoistSettings {
  isEnabled: boolean;
  apiKey: string;
  defaultProjectName: string;
  syncTasks: boolean;
  autoPriority: boolean;
  defaultPriority: string;
}

// 全系統設定整合介面
export interface SystemSettings {
  general: GeneralSettings;
  batch: BatchSettings;
}

// 雞種類型定義
export enum ChickenBreedType {
  BLACK_FEATHER = "BLACK_FEATHER",
  CLASSICAL = "CLASSICAL",
  CAGE_BLACK = "CAGE_BLACK",
  CASTRATED = "CASTRATED",
}

// 批次名稱格式類型
export enum BatchNameFormat {
  DATE_BREED = "YYYYMMDD-BREED",
  BREED_DATE = "BREED-YYYYMMDD",
  DATE_FARM_BREED = "YYYYMMDD-FARM-BREED",
}

// Todoist 優先級類型
export enum TodoistPriority {
  LOW = "1",
  MEDIUM = "2",
  HIGH = "3",
  URGENT = "4",
}

// 設定 API 介面
export interface SettingsAPI {
  fetchSettings: () => Promise<SystemSettings>;
  updateGeneralSettings: (settings: GeneralSettings) => Promise<void>;
  updateBatchSettings: (settings: BatchSettings) => Promise<void>;
  updateTodoistSettings: (settings: TodoistSettings) => Promise<void>;
  testTodoistConnection: (apiKey: string) => Promise<boolean>;
}
