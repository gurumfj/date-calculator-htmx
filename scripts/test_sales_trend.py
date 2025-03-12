import pandas as pd

from cleansales_refactor import Database, settings
from cleansales_refactor.services.query_service import QueryService

pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)
pd.set_option("display.width", None)
pd.set_option("display.max_colwidth", None)


def analyze_batch_sales(batch_name: str = None):
    # 建立資料庫連線
    db = Database(settings.DB_PATH)

    try:
        with db.get_session() as session:
            query_service = QueryService(session)

            if batch_name:
                # 查詢特定批次
                batches = query_service.get_batch_aggregates_by_name(batch_name)
            else:
                # 查詢所有未結案的批次
                batches = query_service.get_not_completed_batches()

            for batch in batches:
                print(f"\n{'=' * 80}")
                print(f"批次：{batch.batch_name}")
                print(f"農場：{batch.farm_name}")
                print(f"狀態：{batch.batch_state.value}")
                print(f"{'=' * 80}")

                trend_data = batch.sales_trend_data
                # print(trend_data["raw"])
                if not isinstance(trend_data["raw"], list):
                    print("此批次尚無銷售資料")
                    continue

                print("\n=== 每日銷售統計 ===")
                daily_df = pd.DataFrame(trend_data["daily"]).T
                print(daily_df)

                print("\n=== 銷售統計摘要 ===")
                print(f"總銷售天數: {len(daily_df)} 天")
                print(f"總銷售公雞: {daily_df['male_count'].sum():,} 隻")
                print(f"總銷售母雞: {daily_df['female_count'].sum():,} 隻")
                total_count = (
                    daily_df["male_count"].sum() + daily_df["female_count"].sum()
                )
                print(f"總銷售數量: {total_count:,} 隻")
                print(
                    f"平均每日銷售: {(daily_df['male_count'] + daily_df['female_count']).mean():.1f} 隻"
                )
                print(f"平均重量: {daily_df['avg_weight'].mean():.2f} kg")
                print(f"總銷售金額: ${daily_df['total_price'].sum():,.0f}")

                # 計算性別比例
                male_ratio = daily_df["male_count"].sum() / total_count * 100
                female_ratio = daily_df["female_count"].sum() / total_count * 100
                print("\n性別比例:")
                print(f"公雞: {male_ratio:.1f}%")
                print(f"母雞: {female_ratio:.1f}%")

                print("\n=== 原始銷售記錄 ===")
                raw_df = pd.DataFrame(trend_data["raw"])
                raw_df["date"] = pd.to_datetime(raw_df["date"]).dt.strftime("%Y-%m-%d")
                print(raw_df.sort_values("date"))

    finally:
        session.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # 如果提供批次名稱，則分析特定批次
        analyze_batch_sales(sys.argv[1])
    else:
        # 否則分析所有未結案的批次
        analyze_batch_sales()
