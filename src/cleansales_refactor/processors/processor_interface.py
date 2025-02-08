from typing import Generic, Protocol, TypeVar

from ..shared.models import ProcessingResult, SourceData

T = TypeVar("T")


class IProcessor(Protocol, Generic[T]):
    """處理器協議"""

    @staticmethod
    def execute(source_data: SourceData) -> ProcessingResult[T]:...

    # @staticmethod
    # def process_data(data: pd.DataFrame) -> ProcessingResult[T]:...
