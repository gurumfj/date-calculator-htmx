from typing import Generic, Protocol, TypeVar

import pandas as pd

from ..models import ProcessingResult

T = TypeVar("T")


class IProcessor(Protocol, Generic[T]):
    """處理器協議"""

    @staticmethod
    def process_data(data: pd.DataFrame) -> ProcessingResult[T]:
        """處理資料並返回結果"""
