import logging
from datetime import date, datetime
from zoneinfo import ZoneInfo

import pandas as pd

logger = logging.getLogger(__name__)

# Consider making this configurable, e.g., from application settings
DEFAULT_LOCAL_TIMEZONE_STR = "Asia/Taipei"

def format_currency(amount: float, round_to: int = 0) -> str:
    """格式化金額"""
    return f"NT$ {amount:,.{round_to}f}"


def day_age(
    breed_date: date | datetime,
    diff_date: date | datetime | pd.Timestamp | None = None,
) -> int:
    """日齡計算函數

    計算從養殖日期到指定日期的天數差異

    Args:
        breed_date (date | datetime): 養殖開始日期
        diff_date (date | datetime | pd.Timestamp | None, optional):
            計算日齡的目標日期，默認為當前本地日期.
            支持 pandas Timestamp 類型以兼容 DataFrame 操作

    Returns:
        int: 日齡天數（包含起始日，所以加1）
    """
    # Use a working variable for diff_date to handle the None case
    actual_diff_date = diff_date

    if actual_diff_date is None:
        local_tz = ZoneInfo(DEFAULT_LOCAL_TIMEZONE_STR)
        actual_diff_date = datetime.now(local_tz).date()

    # Convert breed_date to date type if it's datetime
    if isinstance(breed_date, datetime):
        breed_date = breed_date.date()

    # Convert actual_diff_date to date type if it's datetime or pd.Timestamp
    if isinstance(actual_diff_date, (datetime, pd.Timestamp)):
        actual_diff_date = actual_diff_date.date()
    elif not isinstance(actual_diff_date, date):
        raise TypeError(
            f"Unsupported type for diff_date: {type(actual_diff_date)}. Expected date, datetime, pd.Timestamp, or None."
        )

    # Ensure both are date objects before subtraction
    if not (isinstance(breed_date, date) and isinstance(actual_diff_date, date)):
        raise TypeError("Both breed_date and actual_diff_date must be resolved to date objects for calculation.")

    return (actual_diff_date - breed_date).days + 1


def week_age(day_age: int) -> str:
    """週齡"""
    day = [7, 1, 2, 3, 4, 5, 6]
    return f"{day_age // 7 - 1 if day_age % 7 == 0 else day_age // 7}/{day[day_age % 7]}"
