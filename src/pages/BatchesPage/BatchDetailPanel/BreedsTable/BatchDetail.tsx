import React, { useMemo } from "react";
import { BatchAggregate } from "@app-types";
import { FaUserAlt, FaMapMarkerAlt, FaClipboardList } from "react-icons/fa";
import { COLORS, SPACING } from "./constants/styles";
import { BreedsRecordsTable } from "./BreedsRecordsTable";
import { CustomInfoCard } from "./CustomInfoCard";
/**
 * 批次詳細資訊屬性介面
 */
export interface BatchDetailProps {
  /** 批次聚合資料 */
  batch: BatchAggregate;
  /** 載入狀態 */
  isLoading?: boolean;
  /** 錯誤狀態 */
  error?: Error | null;
}

/**
 * 批次詳細資訊元件
 *
 * 顯示批次的詳細資訊，包括畜牧場、獸醫和入雛資訊等
 */
const BatchDetail: React.FC<BatchDetailProps> = ({
  batch,
  isLoading = false,
  error = null,
}) => {
  // 使用 useMemo 計算批次資訊，避免不必要的重新計算
  const batchInfo = useMemo(() => {
    const firstBreed = batch.breeds[0];
    return {
      farmName: firstBreed?.farm_name ?? "-",
      veterinarian: firstBreed?.veterinarian ?? "-",
      location: firstBreed?.address ?? "-",
      batchType: firstBreed?.chicken_breed ?? "-",
    };
  }, [batch.breeds]);
  // 處理載入狀態
  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="bg-white rounded-xl p-4 text-center">
          <div className="text-sm text-[#8E8E93]">載入中...</div>
        </div>
      </div>
    );
  }

  // 處理錯誤狀態
  if (error) {
    return (
      <div className="space-y-6">
        <div className="bg-white rounded-xl p-4 text-center">
          <div className="text-sm text-red-500">
            載入資料時發生錯誤: {error.message}
          </div>
        </div>
      </div>
    );
  }

  // 處理空資料狀態
  if (!batch || !batch.breeds || batch.breeds.length === 0) {
    return (
      <div className="space-y-6">
        <div className="bg-white rounded-xl p-4 text-center">
          <div className="text-sm text-[#8E8E93]">無批次資料</div>
        </div>
      </div>
    );
  }

  return (
    <div className={SPACING.MARGIN.LG}>
      {/* 詳細資訊區塊 */}
      <div
        className={`${COLORS.BACKGROUND.WHITE} ${SPACING.PADDING.CARD} ${SPACING.MARGIN.MD} rounded-xl`}
      >
        <div className="grid grid-cols-2 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <CustomInfoCard icon={FaUserAlt} title="畜牧場">
            {batchInfo.farmName}
          </CustomInfoCard>
          <CustomInfoCard icon={FaUserAlt} title="獸醫">
            {batchInfo.veterinarian}
          </CustomInfoCard>
          {/* 大螢幕顯示更多資訊 */}
          <CustomInfoCard
            icon={FaMapMarkerAlt}
            title="位置"
            className="hidden lg:flex"
          >
            {batchInfo.location}
          </CustomInfoCard>
          <CustomInfoCard
            icon={FaClipboardList}
            title="品種"
            className="hidden lg:flex"
          >
            {batchInfo.batchType}
          </CustomInfoCard>
        </div>
      </div>

      {/* 入雛資訊表格 */}
      <BreedsRecordsTable batch={batch} isLoading={isLoading} error={error} />
    </div>
  );
};

export default BatchDetail;
