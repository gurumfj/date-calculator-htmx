import React, { Suspense } from "react";
import Settings from "../components/features/settings";

const SettingsPage: React.FC = () => {
  return (
    <div className="p-4">
      <h2 className="text-xl font-semibold mb-4">設定</h2>
      <Suspense fallback={<div className="text-center p-4">載入中...</div>}>
        <Settings />
      </Suspense>
    </div>
  );
};

export default SettingsPage;
