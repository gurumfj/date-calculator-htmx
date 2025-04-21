import React, { useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Loader2, Check, AlertCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import {
  useGeneralSettingsStore,
  defaultGeneralSettings,
} from "../hooks/useGeneralSettingsStore";

// 一般設定區塊，負責管理 API 連線參數與測試
const GeneralSettingsSection: React.FC = () => {
  // 取得 toast 實例，用於全域提示訊息
  const { toast } = useToast();
  // 取得全域設定與操作函數，確保狀態一致性
  const {
    settings: { apiUrl: apiUrlString },
    saveSettings,
    testConnection,
  } = useGeneralSettingsStore();
  // 以目前設定產生 URL 物件，確保初始化參數正確
  const apiUrl = new URL(apiUrlString);
  // 將 URL 各欄位拆分為 state，方便分別綁定 UI 與單獨控制
  const [protocol, setProtocol] = useState(apiUrl.protocol);
  const [hostname, setHostname] = useState(apiUrl.hostname);
  const [port, setPort] = useState(apiUrl.port);
  // 儲存目前組合的 URL，便於即時顯示與驗證
  const [currentUrl, setCurrentUrl] = useState(apiUrl);
  // 管理測試連線的 loading 與狀態，避免多次觸發或狀態錯亂
  const [testingConnection, setTestingConnection] = useState<{
    isLoading: boolean;
    status: boolean | null;
  }>({
    isLoading: false,
    status: null,
  });
  // 控制設定儲存狀態，避免重複點擊
  const [saving, setSaving] = useState(false);

  // 驗證組合後的 URL 是否有效，避免送出錯誤參數
  const validateUrl = useCallback(() => {
    try {
      return new URL(`${protocol}//${hostname}${port ? `:${port}` : ""}`);
    } catch (error) {
      // 捕捉格式錯誤，避免程式崩潰
      console.error("URL解析錯誤:", error);
      return null;
    }
  }, [protocol, hostname, port]);

  const handleTestConnection = async () => {
    const currentUrl = validateUrl();
    if (!currentUrl) {
      toast({
        title: "連線失敗",
        description: "請檢查連線參數是否正確",
        variant: "destructive",
      });
      return;
    }
    setTestingConnection((prev) => ({
      ...prev,
      isLoading: true,
    }));

    try {
      const result = await testConnection(currentUrl);
      if (result) {
        toast({
          title: "連線成功",
          description: "API連線測試成功",
          variant: "default",
        });
        setTestingConnection((prev) => ({
          ...prev,
          status: true,
        }));
      } else {
        toast({
          title: "連線失敗",
          description: "API伺服器返回非健康狀態",
          variant: "destructive",
        });
        setTestingConnection((prev) => ({
          ...prev,
          status: false,
        }));
      }
    } catch (error) {
      console.error("API連線測試失敗:", error);
      toast({
        title: "連線失敗",
        description: "無法連接到API，請檢查連線參數是否正確",
        variant: "destructive",
      });
      setTestingConnection((prev) => ({
        ...prev,
        status: false,
      }));
    } finally {
      setTestingConnection((prev) => ({
        ...prev,
        isLoading: false,
      }));
    }
  };

  useEffect(() => {
    handleTestConnection();
  }, []);

  useEffect(() => {
    const url = validateUrl();
    if (url) {
      setCurrentUrl(url);
    }
  }, [protocol, hostname, port]);

  // 保存設定
  const handleSaveSettings = () => {
    setSaving(true);

    try {
      saveSettings({ apiUrl: currentUrl.toString() });

      toast({
        title: "設定已保存",
        description: "API連線參數已更新",
        variant: "default",
      });
    } catch (error) {
      console.error("保存設定失敗:", error);
      toast({
        title: "保存失敗",
        description: "設定保存時發生錯誤",
        variant: "destructive",
      });
    } finally {
      setSaving(false);
    }
  };

  // 重置設定
  const resetSettings = () => {
    const defaultUrl = new URL(defaultGeneralSettings.apiUrl);
    setProtocol(defaultUrl.protocol);
    setHostname(defaultUrl.hostname);
    setPort(defaultUrl.port);
    setCurrentUrl(defaultUrl);
    handleTestConnection();
    toast({
      title: "設定已重置",
      description: "API連線參數已恢復預設值",
      variant: "default",
    });
  };

  return (
    <div className="grid gap-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>API 設定</span>
            {testingConnection.status !== null && (
              <Badge
                variant={testingConnection.status ? "success" : "destructive"}
              >
                {testingConnection.status ? "已連線" : "未連線"}
              </Badge>
            )}
          </CardTitle>
          <CardDescription>設定API連線參數</CardDescription>
        </CardHeader>

        <CardContent>
          <div className="space-y-4">
            <div>
              <Label htmlFor="api-url">API URL</Label>
              <div className="flex space-x-2 mt-2">
                {/* 協議選擇 */}
                <Select
                  value={protocol}
                  onValueChange={(value) => {
                    setProtocol(value);
                    setTestingConnection((prev) => ({
                      ...prev,
                      status: null,
                    }));
                  }}
                  disabled={testingConnection.isLoading || saving}
                >
                  <SelectTrigger id="protocol" className="w-28">
                    <SelectValue placeholder="協議" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="http:">http://</SelectItem>
                    <SelectItem value="https:">https://</SelectItem>
                  </SelectContent>
                </Select>

                {/* 主機名稱 */}
                <Input
                  id="hostname"
                  placeholder="主機名稱"
                  value={hostname}
                  onChange={(e) => {
                    setHostname(e.target.value);
                    setTestingConnection((prev) => ({
                      ...prev,
                      status: null,
                    }));
                  }}
                  className="flex-1"
                  disabled={testingConnection.isLoading || saving}
                />

                {/* 埠號 */}
                <Input
                  id="port"
                  placeholder="埠號"
                  value={port}
                  onChange={(e) => {
                    setPort(e.target.value);
                    setTestingConnection((prev) => ({
                      ...prev,
                      status: null,
                    }));
                  }}
                  className="w-24"
                  type="number"
                  disabled={testingConnection.isLoading || saving}
                />
              </div>
            </div>

            {/* 顯示完整URL */}
            {currentUrl && (
              <div className="text-sm text-gray-500 flex items-center gap-2">
                <span>完整URL:</span>
                <code className="px-2 py-1 bg-gray-100 rounded-md text-xs">
                  {currentUrl.toString()}
                </code>
                {currentUrl.toString() === apiUrl.toString() && (
                  <span className="flex items-center text-green-600 text-xs">
                    <Check className="h-3 w-3 mr-1" />
                    當前設定
                  </span>
                )}
              </div>
            )}

            {testingConnection.status === true && (
              <div className="p-3 bg-green-50 text-green-700 rounded-md text-sm flex items-center">
                <Check className="h-4 w-4 mr-2" />
                API伺服器運行正常。你可以點擊「保存設定」按鈕儲存此連線參數。
              </div>
            )}

            {testingConnection.status === false && (
              <div className="p-3 bg-red-50 text-red-700 rounded-md text-sm flex items-center">
                <AlertCircle className="h-4 w-4 mr-2" />
                無法連接到API伺服器。請檢查連線參數是否正確，或確認伺服器是否正在運行。
              </div>
            )}
          </div>
        </CardContent>

        <CardFooter className="flex justify-between">
          <Button
            onClick={resetSettings}
            variant="outline"
            className="text-red-500 hover:text-red-700"
            disabled={testingConnection.isLoading || saving}
          >
            恢復預設
          </Button>

          <div>
            {testingConnection.status === true ? (
              <Button
                onClick={handleSaveSettings}
                disabled={saving || testingConnection.isLoading}
              >
                {saving ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    保存中...
                  </>
                ) : (
                  "保存設定"
                )}
              </Button>
            ) : (
              <Button
                onClick={handleTestConnection}
                disabled={testingConnection.isLoading || !hostname || saving}
                className="whitespace-nowrap"
              >
                {testingConnection.isLoading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    測試中...
                  </>
                ) : (
                  "測試連線"
                )}
              </Button>
            )}
          </div>
        </CardFooter>
      </Card>
    </div>
  );
};

export default GeneralSettingsSection;
