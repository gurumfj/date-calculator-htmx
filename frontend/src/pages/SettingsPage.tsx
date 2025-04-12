import React, { Suspense } from "react";
import Settings from "../components/features/settings";
import PageNavbar from "../components/layout/components/PageNavbar";
import { SaveAction } from "../components/layout/components/NavbarIcons";

const SettingsPage: React.FC = () => {
  // 準備右側圖標操作
  const rightActions = (
    <SaveAction title="保存設置" />
  );

  return (
    <>
      {/* 頁面頂部導航欄 */}
      <PageNavbar
        title="設定"
        rightActions={rightActions}
      />

      <div className="p-4">
        <h2 className="text-xl font-semibold mb-4">設定</h2>
        <Suspense fallback={<div className="text-center p-4">載入中...</div>}>
          <Settings />
        </Suspense>
      </div>
    </>
  );
};

export default SettingsPage;
