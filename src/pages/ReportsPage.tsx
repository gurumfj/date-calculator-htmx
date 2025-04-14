import React, { Suspense } from "react";
import PageNavbar from "../components/layout/components/PageNavbar";
import { ChartAction, SearchAction } from "../components/layout/components/NavbarIcons";

const ReportsPage: React.FC = () => {
  // 準備右側圖標操作
  const rightActions = (
    <>
      <SearchAction title="搜索報表" />
      <ChartAction title="圖表視圖" />
    </>
  );

  return (
    <>
      {/* 頁面頂部導航欄 */}
      <PageNavbar 
        title="銷售報表" 
        rightActions={rightActions}
      />
      
      <div className="p-4">
        <h2 className="text-xl font-semibold mb-4">銷售報表</h2>
        <Suspense
          fallback={<div className="text-center p-4">載入中...</div>}
        ></Suspense>
      </div>
    </>
  );
};

export default ReportsPage;
