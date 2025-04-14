// 主要設定頁面元件
import React, { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
// 引入我們的設定組件
import GeneralSettingsSection from "./sections/GeneralSettings";
import BatchSettings from "./sections/BatchSettings";
import TodoistSettings from "@pages/Todoist/TodoistSettings";
import { Toaster } from "@/components/ui/toaster";
import { SaveAction } from "@/components/layout/components/NavbarIcons";
import PageNavbar from "@/components/layout/components/PageNavbar";

export interface SetttingUnit {
  title: string;
  tabValue: string;
  description: string;
  content: React.ReactNode;
}
// 準備右側圖標操作
const rightActions = <SaveAction title="保存設置" />;

const SettingsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState("general");
  const settings: SetttingUnit[] = [
    {
      title: "基本設定",
      tabValue: "general",
      description: "管理各項系統設定與整合服務",
      content: <GeneralSettingsSection />,
    },
    {
      title: "批次設定",
      tabValue: "batch",
      description: "管理批次相關的預設設定與行為",
      content: <BatchSettings />,
    },
    {
      title: "Todoist 整合",
      tabValue: "todoist",
      description: "管理 Todoist 整合設定",
      content: <TodoistSettings />,
    },
  ];

  return (
    <>
      {/* 頁面頂部導航欄 */}
      <PageNavbar title="設定" rightActions={rightActions} />

      <div className="container py-6">
        <div className="flex flex-col space-y-6">
          <div>
            <h1 className="text-2xl font-bold">系統設定</h1>
            <p className="text-muted-foreground">管理各項系統設定與整合服務</p>
          </div>

          <Tabs
            value={activeTab}
            onValueChange={setActiveTab}
            className="w-full"
          >
            <TabsList className="grid w-full md:w-1/2 grid-cols-3 mb-6">
              {settings.map((setting) => (
                <TabsTrigger key={setting.tabValue} value={setting.tabValue}>
                  {setting.title}
                </TabsTrigger>
              ))}
            </TabsList>

            {settings.map((setting) => (
              <TabsContent key={setting.tabValue} value={setting.tabValue}>
                {setting.content}
              </TabsContent>
            ))}
          </Tabs>
        </div>
      </div>
      <Toaster />
    </>
  );
};

export default SettingsPage;
