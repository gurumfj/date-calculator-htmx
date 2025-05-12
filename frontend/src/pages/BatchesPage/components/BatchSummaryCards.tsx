import React, { useMemo } from "react";
/**
 * 批次摘要指標卡片集合
 * Why: 彙整批次關鍵指標，讓用戶快速掌握批次健康、產量、銷售等狀態。
 *      指標選擇依據實際商業需求與用戶最常關心的重點。
 */
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
  FaMars,
  FaVenus,
  FaBalanceScale,
  FaPercent,
  FaDollarSign,
  FaBoxes,
} from "react-icons/fa";
import { BatchAggregateWithRows } from "@app-types";
// import { calculateBatchAggregate } from "@utils/batchCalculations";
import { formatDate } from "@utils/dateUtils";
import { formatCurrency, formatWeight } from "@utils/formatUtils";
import SummaryCard from "./common/SummaryCard";
import {
  calculateMaleRemainder,
  calculateFemaleRemainder,
} from "@utils/batchCalculations";

interface SummaryCardProps {
  batch: BatchAggregateWithRows;
}

/**
 * 批次基本資訊摘要卡片
 */
const BreedSummaryCard: React.FC<SummaryCardProps> = ({ batch }) => {
  const batchInfo = useMemo(
    () => ({
      farmName: batch?.breeds[0]?.farm_name ?? "-",
      veterinarian: batch?.breeds[0]?.veterinarian ?? "-",
      location: batch?.breeds[0]?.address ?? "-",
      batchType: batch?.breeds[0]?.chicken_breed ?? "-",
      license: batch?.breeds[0]?.farm_license ?? "-",
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
      // className: "hidden lg:flex",
    },
    {
      icon: FaClipboardList,
      title: "品種",
      content: batchInfo.batchType,
      // className: "hidden lg:flex",
    },
    {
      icon: FaClipboardList,
      title: "許可證",
      content: batchInfo.license,
      // className: "hidden lg:flex",
    },
  ];

  return <SummaryCard items={items} />;
};

/**
 * 銷售記錄摘要卡片
 */
const SalesSummaryCard: React.FC<SummaryCardProps> = ({ batch }) => {
  const saleInfo = useMemo(() => {
    if (!batch.sales || batch.sales.length === 0)
      return {
        salesPercentage: "-",
        averageWeight: "-",
        averagePrice: "-",
        totalWeight: "-",
        totalIncome: "-",
        maleRemainder: "-",
        femaleRemainder: "-",
      };
    const totalBreedsCount = batch.breeds.reduce(
      (sum, breed) => sum + breed.breed_male + breed.breed_female,
      0
    );
    const totalSalesCount = batch.sales.reduce(
      (sum, sale) => sum + sale.male_count + sale.female_count,
      0
    );
    const averageWeight = () => {
      if (!batch.sales || batch.sales.length === 0) return "-";
      const totalCountWithWeight = batch.sales
        .filter((sale) => sale.total_weight !== null)
        .reduce(
          (sum, sale) => sum + (sale.male_count + sale.female_count || 0),
          0
        );
      const totalWeight = batch.sales.reduce(
        (sum, sale) => sum + (sale.total_weight || 0),
        0
      );
      return totalCountWithWeight > 0
        ? `${(totalWeight / totalCountWithWeight).toFixed(2)} 斤`
        : "-";
    };
    const totalWeight = () => {
      if (!batch.sales || batch.sales.length === 0) return "-";
      const total = batch.sales.reduce(
        (sum, sale) => sum + (sale.total_weight || 0),
        0
      );
      return total > 0 ? `${total.toFixed(1)} 斤` : "-";
    };
    const totalIncome = () => {
      if (!batch.sales || batch.sales.length === 0) return "-";
      const total = batch.sales.reduce(
        (sum, sale) => sum + (sale.total_price || 0),
        0
      );
      return total > 0 ? `${total.toLocaleString("zh-TW")} 元` : "-";
    };
    // const maleRemainder = () => {
    //   if (!batch.sales || batch.sales.length === 0) return "-";
    //   const totalSaleMaleCount = batch.sales.reduce(
    //     (sum, sale) => sum + (sale.male_count || 0),
    //     0
    //   );
    //   const totalBreedMale = batch.breeds.reduce(
    //     (sum, breed) => sum + (breed.breed_male || 0),
    //     0
    //   );
    //   return totalBreedMale * 0.9 - totalSaleMaleCount > 0
    //     ? `${Math.round((totalBreedMale * 0.9 - totalSaleMaleCount) / 100) * 100} 隻`
    //     : "-";
    // };
    // const femaleRemainder = () => {
    //   if (!batch.sales || batch.sales.length === 0) return "-";
    //   const totalSaleFemaleCount = batch.sales.reduce(
    //     (sum, sale) => sum + (sale.female_count || 0),
    //     0
    //   );
    //   const totalBreedFemale = batch.breeds.reduce(
    //     (sum, breed) => sum + (breed.breed_female || 0),
    //     0
    //   );
    //   return totalBreedFemale * 0.94 - totalSaleFemaleCount > 0
    //     ? `${Math.round((totalBreedFemale * 0.94 - totalSaleFemaleCount) / 100) * 100} 隻`
    //     : "-";
    // };
    const averagePrice = () => {
      const totalPrice = batch.sales
        .filter((sale) => sale.total_price !== null)
        .reduce((sum, sale) => sum + (sale.total_price || 0), 0);
      const totalWeight = batch.sales
        .filter((sale) => sale.total_weight !== null)
        .reduce((sum, sale) => sum + (sale.total_weight || 0), 0);
      return totalPrice > 0 && totalWeight > 0
        ? `${(totalPrice / totalWeight).toFixed(2)} 元/斤`
        : "-";
    };

    return {
      salesPercentage:
        totalSalesCount / totalBreedsCount > 0
          ? `${((totalSalesCount / totalBreedsCount) * 100).toFixed(1)}%`
          : "-",
      averageWeight: averageWeight(),
      averagePrice: averagePrice(),
      maleRemainder: calculateMaleRemainder(batch),
      femaleRemainder: calculateFemaleRemainder(batch),
      totalWeight: totalWeight(),
      totalIncome: totalIncome(),
    };
  }, [batch]);

  const items = [
    {
      icon: FaChartLine,
      title: "銷售成數",
      content: saleInfo.salesPercentage,
    },
    {
      icon: FaWeight,
      title: "平均重量",
      content: saleInfo.averageWeight,
    },
    {
      icon: FaWeight,
      title: "平均價格",
      content: saleInfo.averagePrice,
    },
    // {
    //   icon: FaWeight,
    //   title: "已銷售重量",
    //   content: saleInfo.totalWeight,
    //   // className: "hidden lg:flex",
    // },
    {
      icon: FaMoneyBillWave,
      title: "銷售收入",
      content: saleInfo.totalIncome,
      // className: "hidden lg:flex",
    },
    {
      icon: FaMars,
      title: "公雞餘數",
      content: saleInfo.maleRemainder,
    },
    {
      icon: FaVenus,
      title: "母雞餘數",
      content: saleInfo.femaleRemainder,
    },
  ];

  return <SummaryCard items={items} />;
};

/**
 * 飼料記錄摘要卡片
 */
const FeedsSummaryCard: React.FC<SummaryCardProps> = ({ batch }) => {
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

/**
 * 結案記錄摘要卡片
 * Why: 提供批次結案關鍵指標，讓用戶快速掌握批次的最終效益與成果。
 */
const ProductionSummaryCard: React.FC<SummaryCardProps> = ({ batch }) => {
  // 計算結案資料摘要
  const productionInfo = useMemo(() => {
    if (!batch.production || batch.production.length === 0)
      return {
        completionDate: "-",
        saleWeight: "-",
        feedWeight: "-",
        fcr: "-",
        avgPrice: "-",
        revenue: "-",
        costPrice: "-",
        expenses: "-",
        meatCost: "-",
      };

    // 使用最新的結案記錄
    const latestProduction = [...batch.production].sort(
      (a, b) =>
        new Date(b.updated_at || "").getTime() -
        new Date(a.updated_at || "").getTime()
    )[0];

    return {
      completionDate: latestProduction.updated_at
        ? formatDate(latestProduction.updated_at)
        : "-",
      saleWeight: latestProduction.sale_weight_jin
        ? formatWeight(latestProduction.sale_weight_jin)
        : "-",
      feedWeight: latestProduction.feed_weight
        ? latestProduction.feed_weight.toLocaleString() + " KG"
        : "-",
      fcr: latestProduction.fcr ? latestProduction.fcr.toFixed(2) : "-",
      avgPrice: latestProduction.avg_price
        ? formatCurrency(latestProduction.avg_price)
        : "-",
      revenue: latestProduction.revenue
        ? formatCurrency(latestProduction.revenue)
        : "-",
      costPrice: latestProduction.cost_price
        ? formatCurrency(latestProduction.cost_price)
        : "-",
      expenses: latestProduction.expenses
        ? formatCurrency(latestProduction.expenses)
        : "-",
      meatCost: latestProduction.meat_cost
        ? formatCurrency(latestProduction.meat_cost)
        : "-",
      profit:
        latestProduction.revenue && latestProduction.expenses
          ? formatCurrency(
              latestProduction.revenue - (latestProduction.expenses || 0)
            )
          : "-",
      profitMargin:
        latestProduction.revenue &&
        latestProduction.expenses &&
        latestProduction.revenue > 0
          ? `${(((latestProduction.revenue - (latestProduction.expenses || 0)) / latestProduction.revenue) * 100).toFixed(1)}%`
          : "-",
    };
  }, [batch.production]);

  const items = [
    {
      icon: FaBalanceScale,
      title: "飼料效率",
      content: productionInfo.fcr,
    },
    {
      icon: FaDollarSign,
      title: "造肉成本",
      content: productionInfo.meatCost,
    },
    {
      icon: FaDollarSign,
      title: "平均單價",
      content: productionInfo.avgPrice,
    },
    {
      icon: FaDollarSign,
      title: "成本單價",
      content: productionInfo.costPrice,
    },
    {
      icon: FaUtensils,
      title: "飼料重量",
      content: productionInfo.feedWeight,
    },
    {
      icon: FaBoxes,
      title: "銷售重量",
      content: productionInfo.saleWeight,
    },
    {
      icon: FaMoneyBillWave,
      title: "總收入",
      content: productionInfo.revenue,
    },
    {
      icon: FaDollarSign,
      title: "成本價格",
      content: productionInfo.costPrice,
      className: "hidden lg:flex",
    },
    {
      icon: FaMoneyBillWave,
      title: "利潤",
      content: productionInfo.profit,
    },
    {
      icon: FaPercent,
      title: "利潤率",
      content: productionInfo.profitMargin,
    },
  ];

  return <SummaryCard items={items} />;
};

export {
  BreedSummaryCard,
  SalesSummaryCard,
  FeedsSummaryCard,
  ProductionSummaryCard,
};
