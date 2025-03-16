from datetime import date, datetime

import pandas as pd


def format_currency(amount: float, round_to: int = 0) -> str:
    """格式化金額"""
    return f"NT$ {amount:,.{round_to}f}"


def day_age(
    breed_date: date | datetime,
    diff_date: date | datetime | pd.Timestamp = datetime.now().date(),
) -> int:
    """日齡計算函數

    計算從養殖日期到指定日期的天數差異

    Args:
        breed_date (date | datetime): 養殖開始日期
        diff_date (date | datetime | pd.Timestamp, optional):
            計算日齡的目標日期，默認為當前日期
            支持 pandas Timestamp 類型以兼容 DataFrame 操作

    Returns:
        int: 日齡天數（包含起始日，所以加1）
    """
    if isinstance(breed_date, datetime):
        breed_date = breed_date.date()
    # 增加對 pandas Timestamp 的支持
    if isinstance(diff_date, (datetime, pd.Timestamp)):
        diff_date = diff_date.date()
    return (diff_date - breed_date).days + 1


def week_age(day_age: int) -> str:
    """週齡"""
    day = [7, 1, 2, 3, 4, 5, 6]
    return (
        f"{day_age // 7 - 1 if day_age % 7 == 0 else day_age // 7}/{day[day_age % 7]}"
    )
