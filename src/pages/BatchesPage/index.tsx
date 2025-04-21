import React, { useEffect, useRef, useState } from "react";
import { useBatchStore } from "./store/useBatchStore";
import { BatchCard, BatchFilters, BatchDetailPanel } from "./components";
import { useFetchBatchAggregatesIndex } from "./hooks";
import PageNavbar from "@/components/layout/components/PageNavbar";
import { useParams } from "react-router-dom";
import BackButton from "@/components/layout/components/BackButton";

// BatchesPage 為批次管理主頁，結合查詢、篩選、卡片、詳情等功能
// 採用組合式元件設計，利於擴充與維護
// 條件渲染設計，提升桌面與行動裝置體驗

// BatchesPage 作為批次管理主頁，整合查詢、篩選、卡片顯示等功能
// 採用組合式設計，方便未來擴充與維護
const BatchesPage: React.FC = () => {
  // ================== 狀態與 hooks 定義區 ==================
  // 1. 全域 store 狀態
  const { filter, selectedBatchName, setSelectedBatchName } = useBatchStore();
  // 2. 本地狀態
  const [mobileView, setMobileView] = useState(false);
  // 3. Refs
  const selectedCardRef = useRef<HTMLDivElement>(null);
  // 4. Router 參數
  const { batchName } = useParams<{ batchName: string }>();
  // 5. React Query hooks
  const {
    data: batchIndice = [],
    isLoading,
    isError,
  } = useFetchBatchAggregatesIndex(filter);

  // ================== 副作用 useEffect 區 ==================
  // 響應式切換 mobile/desktop UI
  useEffect(() => {
    const handleResize = () => {
      setMobileView(window.innerWidth < 768);
    };
    window.addEventListener("resize", handleResize);
    handleResize(); // 初始判斷
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  // 批次卡片自動捲動到選中位置
  useEffect(() => {
    if (selectedBatchName && selectedCardRef.current) {
      selectedCardRef.current.scrollIntoView({
        behavior: "smooth",
        block: "nearest",
        inline: "nearest",
      });
    }
  }, [selectedBatchName, batchIndice]);

  // URL 控制 store 狀態，確保 UI 與網址同步
  useEffect(() => {
    if (batchName) {
      setSelectedBatchName(batchName);
    } else {
      setSelectedBatchName(null);
    }
    // Why: 保證刷新/返回/分享時 UI 狀態與 URL 完全一致
  }, [batchName, setSelectedBatchName]);

  // ================== 渲染區段 ==================
  if (isLoading || isError) {
    // Why: loading 狀態下顯示提示，避免用戶誤解為空資料
    return <div>loading...</div>;
  }

  // 返回按鈕元件，僅在已選批次時顯示，提升 UX
  const backButton = <BackButton title="返回" iconOnly={true} />;

  // --- 行動裝置視圖 ---
  if (mobileView) {
    return (
      <div className="p-2">
        {/* 根據是否選擇批次，決定 Navbar 樣式與返回操作（提升返回體驗） */}
        <PageNavbar
          title="批次管理"
          {...(selectedBatchName ? { leftActions: backButton } : {})}
        />
        {/* 未選批次時顯示篩選條件，查詢與主內容分離，易於維護 */}
        {!selectedBatchName && <BatchFilters />}
        {/* 未選批次且有資料時顯示批次卡片列表，保持主頁清爽，避免資訊過載 */}
        {!selectedBatchName && batchIndice?.length > 0 && (
          <div className="p-2 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {batchIndice.map((batchIndex) => (
              // 使用 batch_name 作為 key，確保唯一性與效能
              <BatchCard
                key={batchIndex.batch_name}
                batchName={batchIndex.batch_name}
              />
            ))}
          </div>
        )}
        {/* 已選批次時顯示詳情面板，避免主頁資訊干擾，聚焦單一批次 */}
        {selectedBatchName && <BatchDetailPanel />}
      </div>
    );
  }

  // --- 桌面端視圖 ---
  return (
    <div className="p-2">
      {/* 桌面端標題列與篩選條件固定於頂部，保持一致性 */}
      <PageNavbar title="批次管理" />
      <BatchFilters />
      {selectedBatchName ? (
        // 有選擇批次時，左右分欄顯示，提升資訊瀏覽效率
        <div className="flex gap-4 mt-2">
          {/* 左側：批次卡片列表，限制高度並可滾動，避免詳情遮蔽 */}
          <div className="p-2 w-1/3 max-h-[90vh] overflow-y-auto border-r pr-4 flex flex-col gap-4">
            {batchIndice?.length > 0 ? (
              // 使用 batch_name 作為 key，確保唯一性與效能
              batchIndice.map((batchIndex) => (
                <div
                  key={batchIndex.batch_name}
                  ref={
                    batchIndex.batch_name === selectedBatchName
                      ? selectedCardRef
                      : null
                  }
                >
                  <BatchCard
                    key={batchIndex.batch_name}
                    batchName={batchIndex.batch_name}
                  />
                </div>
              ))
            ) : (
              <div className="text-center">沒有批次資料</div>
            )}
          </div>
          {/* 右側：批次詳情面板，固定於右欄，避免主頁資訊干擾 */}
          <div className="flex-1 pl-4">
            <BatchDetailPanel />
          </div>
        </div>
      ) : (
        // 未選擇批次時，維持原本網格列表樣式，清爽易讀
        <div className="p-2 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {batchIndice?.length > 0 ? (
            // 使用 batch_name 作為 key，確保唯一性與效能
            batchIndice.map((batchIndex) => (
              <BatchCard
                key={batchIndex.batch_name}
                batchName={batchIndex.batch_name}
              />
            ))
          ) : (
            <div className="text-center">沒有批次資料</div>
          )}
        </div>
      )}
    </div>
  );
};

// Why: 保持單一出口，方便後續維護與測試
export default BatchesPage;
