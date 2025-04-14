import React, { Suspense } from "react";
import PageNavbar from "@components/layout/components/PageNavbar";
import {
  SearchAction,
  SettingsAction,
} from "@components/layout/components/NavbarIcons";
import TodoistPage from "@pages/Todoist";

const HomePage: React.FC = () => {
  // 示範右側圖標操作
  const rightActions = (
    <>
      <SearchAction title="搜索數據" />
      <SettingsAction title="儀表盤設置" />
    </>
  );

  return (
    <>
      {/* 頁面頂部導航欄 */}
      <PageNavbar title="儀表盤" rightActions={rightActions} />
      <Suspense fallback={<div className="text-center p-4">載入中...</div>}>
        {/* <Dashboard /> */}
        <TodoistPage batch={null} />
      </Suspense>
    </>
  );
};

export default HomePage;
