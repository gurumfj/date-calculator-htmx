import React, { Suspense } from "react";
import PageNavbar from "../components/layout/components/PageNavbar";
import { SearchAction, SettingsAction } from "../components/layout/components/NavbarIcons";
// 我們也可以直接使用 HeroIcons，示範兩種方式
// import { MagnifyingGlassIcon, Cog6ToothIcon } from "@heroicons/react/24/outline";
// import NavbarAction from "../components/layout/components/NavbarAction";

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
      <PageNavbar 
        title="儀表盤" 
        rightActions={rightActions}
      />
      
      <div className="p-4">
        <h2 className="text-xl font-semibold mb-4">儀表盤</h2>
        <Suspense fallback={<div className="text-center p-4">載入中...</div>}>
          {/* <Dashboard /> */}
        </Suspense>
        
        <div className="bg-white p-4 rounded-lg shadow mt-4">
          <h3 className="text-lg font-medium mb-2">使用導航欄圖標說明</h3>
          <p className="text-gray-600 mb-2">
            導航欄現在支持圖標操作，您可以在頁面中看到右上角的搜索和設置圖標。
          </p>
          <p className="text-gray-600">
            這些圖標提供了一種簡潔的方式來顯示常用操作，當鼠標懸停在圖標上時會顯示相應的提示文字。
          </p>
        </div>
      </div>
    </>
  );
};

export default HomePage;
