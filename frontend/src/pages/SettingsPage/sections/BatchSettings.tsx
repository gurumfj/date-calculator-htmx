import React, { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { useSettings } from "../useSettingStore";
import { BatchSettings as BatchSettingsType } from "../types";

// 導入必要的 UI 元件
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";

export default function BatchSettings() {
  const { toast } = useToast();
  const { settings, isLoading, setBatchSettings, saveSettings } = useSettings();

  const [localSettings, setLocalSettings] = useState<BatchSettingsType>(
    settings.batch
  );

  // 當設定變更時更新本地狀態
  useEffect(() => {
    setLocalSettings(settings.batch);
  }, [settings.batch]);

  // 保存設定
  const handleSave = async () => {
    try {
      setBatchSettings(localSettings);
      await saveSettings();

      toast({
        title: "設定已保存",
        description: "批次設定已成功更新",
      });
    } catch (error) {
      console.error("Error saving settings:", error);
      toast({
        title: "保存失敗",
        description: "設定保存時發生錯誤，請稍後再試",
        variant: "destructive",
      });
    }
  };

  // 更新本地設定
  const updateSettings = (updates: Partial<BatchSettingsType>) => {
    setLocalSettings((prev) => ({ ...prev, ...updates }));
  };

  return (
    <div className="grid gap-6">
      <Card>
        <CardHeader>
          <CardTitle>批次設定</CardTitle>
          <CardDescription>管理批次相關的預設設定與行為</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="defaultChickenBreed">預設雞種</Label>
            <Select
              value={localSettings.defaultChickenBreed}
              onValueChange={(value: string) =>
                updateSettings({ defaultChickenBreed: value })
              }
            >
              <SelectTrigger>
                <SelectValue placeholder="選擇預設雞種" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="BLACK_FEATHER">黑羽</SelectItem>
                <SelectItem value="CLASSICAL">古早</SelectItem>
                <SelectItem value="CAGE_BLACK">舍黑</SelectItem>
                <SelectItem value="CASTRATED">閹雞</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="defaultFarmLocation">預設場區</Label>
            <Input
              id="defaultFarmLocation"
              value={localSettings.defaultFarmLocation}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                updateSettings({ defaultFarmLocation: e.target.value })
              }
              placeholder="請輸入預設場區名稱"
            />
          </div>

          <Separator />

          <div className="flex flex-col space-y-4">
            <div className="flex items-center space-x-2">
              <Switch
                id="autoGenerateBatchNames"
                checked={localSettings.autoGenerateBatchNames}
                onCheckedChange={(checked: boolean) =>
                  updateSettings({ autoGenerateBatchNames: checked })
                }
              />
              <Label htmlFor="autoGenerateBatchNames">自動生成批次名稱</Label>
            </div>

            {localSettings.autoGenerateBatchNames && (
              <div className="space-y-2 pl-6">
                <Label htmlFor="batchNameFormat">批次名稱格式</Label>
                <Select
                  value={localSettings.batchNameFormat}
                  onValueChange={(value: string) =>
                    updateSettings({ batchNameFormat: value })
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="選擇批次名稱格式" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="YYYYMMDD-BREED">
                      日期-品種 (20240414-黑羽)
                    </SelectItem>
                    <SelectItem value="BREED-YYYYMMDD">
                      品種-日期 (黑羽-20240414)
                    </SelectItem>
                    <SelectItem value="YYYYMMDD-FARM-BREED">
                      日期-場區-品種 (20240414-主場-黑羽)
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>
            )}
          </div>

          <div className="flex items-center space-x-2">
            <Switch
              id="autoCompleteAfterSale"
              checked={localSettings.autoCompleteAfterSale}
              onCheckedChange={(checked: boolean) =>
                updateSettings({ autoCompleteAfterSale: checked })
              }
            />
            <Label htmlFor="autoCompleteAfterSale">
              銷售完畢後自動標記批次為完成
            </Label>
          </div>
        </CardContent>
        <CardFooter>
          <Button onClick={handleSave} disabled={isLoading}>
            {isLoading ? "保存中..." : "保存設定"}
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
}
