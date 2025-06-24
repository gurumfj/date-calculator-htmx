import json
from typing import List, Union

from fastapi import Request

from .models import DateData, DateInterval


def get_session_store(request: Request) -> List[Union[DateData, DateInterval]]:
    """Get date calculations from session"""
    if not hasattr(request, "session"):
        return []

    store_json = request.session.get("date_store", [])
    results = []

    for json_str in store_json:
        data = json.loads(json_str)
        # 根據類型標記決定使用哪個類別
        if data.get("type") == "interval":
            results.append(DateInterval.from_dict(data))
        else:
            results.append(DateData.from_dict(data))

    return results


def save_to_session(request: Request, store: List[Union[DateData, DateInterval]]):
    """Save date calculations to session"""
    if not hasattr(request, "session"):
        return

    request.session["date_store"] = [data.to_json() for data in store]
