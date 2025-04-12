import React, { useMemo } from "react";
import {
  FaUserAlt,
  FaMapMarkerAlt,
  FaClipboardList,
  FaChartLine,
  FaCalendarAlt,
  FaMoneyBillWave,
  FaWeight,
  FaUtensils,
  FaClipboardCheck,
} from "react-icons/fa";
import { BatchAggregate } from "@app-types";
// import { calculateBatchAggregate } from "@utils/batchCalculations";
import { formatDate } from "@utils/dateUtils";
import SummaryCard from "./SummaryCard";

interface SummaryCardProps {
  batch: BatchAggregate;
}

/**
 * 批次基本資訊摘要卡片
 */
export const BreedSummaryCard: React.FC<SummaryCardProps> = ({ batch }) => {
  const batchInfo = useMemo(
    () => ({
      farmName: batch?.breeds[0]?.farm_name ?? "-",
      veterinarian: batch?.breeds[0]?.veterinarian ?? "-",
      location: batch?.breeds[0]?.address ?? "-",
      batchType: batch?.breeds[0]?.chicken_breed ?? "-",
    }),
    [batch?.breeds]
  );

  const items = [
    {
      icon: FaUserAlt,
      title: "畜牧場",
      content: batchInfo.farmName,
    },
    {
      icon: FaUserAlt,
      title: "獸醫",
      content: batchInfo.veterinarian,
    },
    {
      icon: FaMapMarkerAlt,
      title: "位置",
      content: batchInfo.location,
      className: "hidden lg:flex",
    },
    {
      icon: FaClipboardList,
      title: "品種",
      content: batchInfo.batchType,
      className: "hidden lg:flex",
    },
  ];

  return <SummaryCard items={items} />;
};

/**
 * 銷售記錄摘要卡片
 */
export const SalesSummaryCard: React.FC<SummaryCardProps> = ({ batch }) => {
  // 計算批次銷售摘要數據
  // const batchAggregate = useMemo(() => calculateBatchAggregate(batch), [batch]);

  // 計算總銷售數量
  const totalSales = useMemo(() => {
    if (!batch.sales || batch.sales.length === 0) return 0;
    return batch.sales.length;
  }, [batch.sales]);

  // 計算最近銷售日期
  const latestSaleDate = useMemo(() => {
    if (!batch.sales || batch.sales.length === 0) return "-";
    const sortedSales = [...batch.sales].sort(
      (a, b) =>
        new Date(b.sale_date).getTime() - new Date(a.sale_date).getTime()
    );
    return formatDate(sortedSales[0].sale_date);
  }, [batch.sales]);

  // 計算總銷售重量
  const totalWeight = useMemo(() => {
    if (!batch.sales || batch.sales.length === 0) return "-";
    const total = batch.sales.reduce(
      (sum, sale) => sum + (sale.total_weight || 0),
      0
    );
    return total > 0 ? `${total.toFixed(1)} 斤` : "-";
  }, [batch.sales]);

  // 計算總銷售收入 (假設有銷售收入數據)
  const totalIncome = useMemo(() => {
    // 這裡需要根據實際數據結構計算總收入
    // 示例：return `${income.toFixed(0)} 元`;
    return "-";
  }, [batch.sales]);

  const items = [
    {
      icon: FaChartLine,
      title: "總銷售數",
      content: totalSales || "-",
    },
    {
      icon: FaCalendarAlt,
      title: "最近銷售",
      content: latestSaleDate,
    },
    {
      icon: FaWeight,
      title: "已銷售重量",
      content: totalWeight,
      className: "hidden lg:flex",
    },
    {
      icon: FaMoneyBillWave,
      title: "銷售收入",
      content: totalIncome,
      className: "hidden lg:flex",
    },
  ];

  return <SummaryCard items={items} />;
};

/**
 * 飼料記錄摘要卡片
 */
export const FeedsSummaryCard: React.FC<SummaryCardProps> = ({ batch }) => {
  // 計算飼料種類數
  const feedTypes = useMemo(() => {
    if (!batch.feeds || batch.feeds.length === 0) return 0;
    const types = new Set(batch.feeds.map((feed) => feed.feed_item));
    return types.size;
  }, [batch.feeds]);

  // 計算最近飼料更換日期
  const latestFeedChange = useMemo(() => {
    if (!batch.feeds || batch.feeds.length === 0) return "-";
    const sortedFeeds = [...batch.feeds].sort(
      (a, b) =>
        new Date(b.feed_date).getTime() - new Date(a.feed_date).getTime()
    );
    return formatDate(sortedFeeds[0].feed_date);
  }, [batch.feeds]);

  // 計算已完成和進行中的飼料項目數
  const completedItems = useMemo(() => {
    if (!batch.feeds || batch.feeds.length === 0) return 0;
    return batch.feeds.filter((feed) => feed.is_completed).length;
  }, [batch.feeds]);

  const ongoingItems = useMemo(() => {
    if (!batch.feeds || batch.feeds.length === 0) return 0;
    return batch.feeds.filter((feed) => !feed.is_completed).length;
  }, [batch.feeds]);

  const items = [
    {
      icon: FaUtensils,
      title: "飼料種類數",
      content: feedTypes || "-",
    },
    {
      icon: FaCalendarAlt,
      title: "最近飼料更換",
      content: latestFeedChange,
    },
    {
      icon: FaClipboardCheck,
      title: "已完成項目",
      content: completedItems || "-",
      className: "hidden lg:flex",
    },
    {
      icon: FaClipboardList,
      title: "進行中項目",
      content: ongoingItems || "-",
      className: "hidden lg:flex",
    },
  ];

  return <SummaryCard items={items} />;
};
