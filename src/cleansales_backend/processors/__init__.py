from dataclasses import dataclass
from typing import Protocol

from .breeds_schema import BreedRecordORM, BreedRecordProcessor
from .feeds_schema import FeedRecordORM, FeedRecordProcessor
from .interface.breed_repository_protocol import BreedRepositoryProtocol
from .interface.feed_repository_protocol import FeedRepositoryProtocol
from .interface.processors_interface import IBaseModel, IORMModel, IProcessor, IResponse
from .interface.sale_repository_protocol import SaleRepositoryProtocol
from .sales_schema import SaleRecordORM, SaleRecordProcessor


class IRespositoryService(Protocol):
    breed_repository: BreedRepositoryProtocol
    sale_repository: SaleRepositoryProtocol
    feed_repository: FeedRepositoryProtocol


@dataclass
class RespositoryServiceImpl:
    breed_repository: BreedRepositoryProtocol = BreedRecordProcessor()
    sale_repository: SaleRepositoryProtocol = SaleRecordProcessor()
    feed_repository: FeedRepositoryProtocol = FeedRecordProcessor()


__all__ = [
    "IProcessor",
    "IRespositoryService",
    "RespositoryServiceImpl",
    "BreedRecordProcessor",
    "FeedRecordProcessor",
    "SaleRecordProcessor",
    "IBaseModel",
    "IORMModel",
    "IResponse",
    "BreedRepositoryProtocol",
    "SaleRepositoryProtocol",
    "FeedRepositoryProtocol",
    "BreedRecordORM",
    "SaleRecordORM",
    "FeedRecordORM",
]
