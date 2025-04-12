import React, { useState } from "react";
import { Field, Switch, Label } from "@headlessui/react";
import {
  FaQuestion,
  FaInfoCircle,
  FaExternalLinkAlt,
  FaSync,
  FaDatabase,
  FaBell,
  FaClock,
} from "react-icons/fa";

interface SettingsProps {
  customSettings?: Record<string, unknown>;
}

const Settings: React.FC<SettingsProps> = () => {
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [notifications, setNotifications] = useState(true);
  const [offlineMode, setOfflineMode] = useState(false);
  const [debugMode, setDebugMode] = useState(false);
  const [compactMode, setCompactMode] = useState(false);

  // 系统信息
  const appVersion = "1.0.0";
  const lastSync = new Date().toLocaleString();

  return (
    <div className="space-y-6">
      {/* 设置区域 */}
      <div className="bg-white rounded-lg shadow-sm">
        <div className="p-4 border-b">
          <h3 className="text-lg font-medium text-gray-800">顯示設定</h3>
        </div>

        <div className="p-4 space-y-3">
          <Field className="flex items-center justify-between p-2 hover:bg-gray-50 rounded">
            <div className="flex items-center space-x-3">
              <FaSync className="text-green-500" />
              <Label className="text-gray-700">自動重新整理</Label>
            </div>
            <Switch
              checked={autoRefresh}
              onChange={setAutoRefresh}
              className={`${
                autoRefresh ? "bg-blue-500" : "bg-gray-200"
              } relative inline-flex h-6 w-11 items-center rounded-full transition-colors`}
            >
              <span
                className={`${
                  autoRefresh ? "translate-x-6" : "translate-x-1"
                } inline-block h-4 w-4 transform rounded-full bg-white transition-transform`}
              />
            </Switch>
          </Field>

          <Field className="flex items-center justify-between p-2 hover:bg-gray-50 rounded">
            <div className="flex items-center space-x-3">
              <FaDatabase className="text-purple-500" />
              <div>
                <Label className="text-gray-700">離線模式</Label>
                <p className="text-xs text-gray-500">僅使用本地快取資料</p>
              </div>
            </div>
            <Switch
              checked={offlineMode}
              onChange={setOfflineMode}
              className={`${
                offlineMode ? "bg-blue-500" : "bg-gray-200"
              } relative inline-flex h-6 w-11 items-center rounded-full transition-colors`}
            >
              <span
                className={`${
                  offlineMode ? "translate-x-6" : "translate-x-1"
                } inline-block h-4 w-4 transform rounded-full bg-white transition-transform`}
              />
            </Switch>
          </Field>

          <Field className="flex items-center justify-between p-2 hover:bg-gray-50 rounded">
            <div className="flex items-center space-x-3">
              <FaBell className="text-red-500" />
              <Label className="text-gray-700">通知提醒</Label>
            </div>
            <Switch
              checked={notifications}
              onChange={setNotifications}
              className={`${
                notifications ? "bg-blue-500" : "bg-gray-200"
              } relative inline-flex h-6 w-11 items-center rounded-full transition-colors`}
            >
              <span
                className={`${
                  notifications ? "translate-x-6" : "translate-x-1"
                } inline-block h-4 w-4 transform rounded-full bg-white transition-transform`}
              />
            </Switch>
          </Field>
        </div>
      </div>

      {/* 系统信息 */}
      <div className="bg-white rounded-lg shadow-sm">
        <div className="p-4 border-b">
          <h3 className="text-lg font-medium text-gray-800">系統資訊</h3>
        </div>

        <div className="p-4 space-y-3">
          <div className="flex justify-between items-center p-2">
            <span className="text-gray-600">應用版本</span>
            <span className="text-gray-900 font-medium">{appVersion}</span>
          </div>

          <div className="flex justify-between items-center p-2">
            <span className="text-gray-600">最後同步時間</span>
            <span className="text-gray-900 font-medium">{lastSync}</span>
          </div>

          <div className="flex justify-between items-center p-2">
            <span className="text-gray-600">API 狀態</span>
            <span className="text-green-600 font-medium flex items-center">
              <span className="w-2 h-2 rounded-full bg-green-500 mr-2"></span>
              正常
            </span>
          </div>
        </div>
      </div>

      {/* 進階設定 */}
      <div className="bg-white rounded-lg shadow-sm">
        <div className="p-4 border-b">
          <h3 className="text-lg font-medium text-gray-800">進階設定</h3>
        </div>

        <div className="p-4 space-y-3">
          <Field className="flex items-center justify-between p-2 hover:bg-gray-50 rounded">
            <div className="flex items-center space-x-3">
              <FaQuestion className="text-blue-500" />
              <div>
                <Label className="text-gray-700">除錯模式</Label>
                <p className="text-xs text-gray-500">顯示額外的除錯資訊</p>
              </div>
            </div>
            <Switch
              checked={debugMode}
              onChange={setDebugMode}
              className={`${
                debugMode ? "bg-blue-500" : "bg-gray-200"
              } relative inline-flex h-6 w-11 items-center rounded-full transition-colors`}
            >
              <span
                className={`${
                  debugMode ? "translate-x-6" : "translate-x-1"
                } inline-block h-4 w-4 transform rounded-full bg-white transition-transform`}
              />
            </Switch>
          </Field>

          <Field className="flex items-center justify-between p-2 hover:bg-gray-50 rounded">
            <div className="flex items-center space-x-3">
              <FaDatabase className="text-orange-500" />
              <Label className="text-gray-700">清除本地快取</Label>
            </div>
            <button
              className="px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded text-sm font-medium"
              onClick={() => {
                if (
                  window.confirm("確定要清除本地快取嗎？這將移除所有離線資料。")
                ) {
                  localStorage.clear();
                  alert("快取已清除，應用將重新載入");
                  window.location.reload();
                }
              }}
            >
              清除
            </button>
          </Field>

          <Field className="flex items-center justify-between p-2 hover:bg-gray-50 rounded">
            <div className="flex items-center space-x-3">
              <FaClock className="text-teal-500" />
              <div>
                <Label className="text-gray-700">緊湊模式</Label>
                <p className="text-xs text-gray-500">減少間距，顯示更多內容</p>
              </div>
            </div>
            <Switch
              checked={compactMode}
              onChange={setCompactMode}
              className={`${
                compactMode ? "bg-blue-500" : "bg-gray-200"
              } relative inline-flex h-6 w-11 items-center rounded-full transition-colors`}
            >
              <span
                className={`${
                  compactMode ? "translate-x-6" : "translate-x-1"
                } inline-block h-4 w-4 transform rounded-full bg-white transition-transform`}
              />
            </Switch>
          </Field>
        </div>
      </div>

      {/* 關於 */}
      <div className="bg-white rounded-lg shadow-sm p-4">
        <div className="text-center space-y-2">
          <h3 className="text-lg font-medium text-gray-800">關於 CleanSales</h3>
          <p className="text-sm text-gray-600">
            © 2025 CleanSales 雞禽養殖管理系統
          </p>
          <p className="text-xs text-gray-500">版本 {appVersion}</p>

          <div className="flex justify-center space-x-4 pt-2">
            <a
              href="#"
              className="text-blue-500 hover:text-blue-700 flex items-center text-sm"
            >
              <FaInfoCircle className="mr-1" /> 使用說明
            </a>
            <a
              href="#"
              className="text-blue-500 hover:text-blue-700 flex items-center text-sm"
            >
              <FaExternalLinkAlt className="mr-1" /> 開發者網站
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;
