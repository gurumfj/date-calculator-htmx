# from .breeds_processor import BreedsProcessor
from .breeds_schema import BreedRecordORM, BreedRecordProcessor
from .feeds_schema import FeedRecordORM, FeedRecordProcessor
from .interface.breed_repository_protocol import BreedRepositoryProtocol
from .interface.feed_repository_protocol import FeedRepositoryProtocol
from .interface.processors_interface import IBaseModel, IORMModel, IProcessor, IResponse
from .interface.sale_repository_protocol import SaleRepositoryProtocol
from .sales_schema import SaleRecordORM, SaleRecordProcessor

__all__ = [
    "IProcessor",
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
