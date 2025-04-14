import React, { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Loader2 } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import todoistApi from "@/lib/todoistApis";
import { Project } from "./types";
import { useTodoistSettingsStore } from "./hooks/useTodoistSettingStore";

/**
 * Todoist設置頁面
 * 樣式與GeneralSettings一致
 */
const TodoistSettingsPage: React.FC = () => {
  const { toast } = useToast();
  const { settings, saveSettings } = useTodoistSettingsStore();
  const [currentProject, setCurrentProject] = useState<string>(
    settings.defaultProjectId || ""
  );
  const [isLoading, setIsLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [projects, setProjects] = useState<Project[]>([]);

  const handleFetchProjects = async () => {
    setIsLoading(true);
    try {
      const projects = await todoistApi.getProjects();
      return projects;
    } catch (error) {
      console.error("Error fetching projects:", error);
      return [];
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    handleFetchProjects().then((projects) => setProjects(projects));
  }, []);

  // 處理選擇變更
  const handleProjectChange = (value: string) => {
    setCurrentProject(value);
  };

  // 保存設定
  const handleSaveSettings = () => {
    setSaving(true);
    saveSettings({
      defaultProjectId: currentProject,
    });
    toast({
      title: "設定已保存",
      description: "Todoist設定已保存",
      variant: "default",
    });
    setSaving(false);
  };

  // 重置設定
  const handleResetSettings = () => {
    setCurrentProject(settings.defaultProjectId || "");
    toast({
      title: "設定已重置",
      description: "Todoist設定已恢復預設值",
      variant: "default",
    });
  };

  return (
    <div className="grid gap-6">
      <Card>
        <CardHeader>
          <CardTitle>Todoist 設定</CardTitle>
          <CardDescription>設定 Todoist 整合選項</CardDescription>
        </CardHeader>

        <CardContent>
          <div className="space-y-4">
            <div>
              <Label htmlFor="default-project">預設專案</Label>
              <div className="mt-2">
                <Select
                  value={currentProject}
                  onValueChange={handleProjectChange}
                  disabled={isLoading || saving}
                >
                  <SelectTrigger id="default-project">
                    <SelectValue placeholder="選擇預設專案" />
                  </SelectTrigger>
                  <SelectContent>
                    {projects.map((project) => (
                      <SelectItem key={project.id} value={project.id}>
                        {project.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <p className="text-sm text-gray-500 mt-2">
                選擇創建新任務時的預設專案。未選擇時將使用Todoist的收件匣。
              </p>
            </div>
          </div>
        </CardContent>

        <CardFooter className="flex justify-between">
          <Button
            onClick={handleResetSettings}
            variant="outline"
            className="text-red-500 hover:text-red-700"
            disabled={isLoading || saving}
          >
            恢復預設
          </Button>

          <Button onClick={handleSaveSettings} disabled={isLoading || saving}>
            {saving ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                保存中...
              </>
            ) : (
              "保存設定"
            )}
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
};

export default TodoistSettingsPage;
