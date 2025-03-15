# from .breeds_processor import BreedsProcessor
from .breeds_schema import BreedRecordProcessor, BreedRecordORM
from .interface.breed_repository_protocol import BreedRepositoryProtocol
from .interface.processors_interface import IBaseModel, IORMModel, IProcessor, IResponse
from .interface.sale_repository_protocol import SaleRepositoryProtocol
from .sales_schema import SaleRecordProcessor, SaleRecordORM

__all__ = [
    "IProcessor",
    "BreedRecordProcessor",
    "SaleRecordProcessor",
    "IBaseModel",
    "IORMModel",
    "IResponse",
    "BreedRepositoryProtocol",
    "SaleRepositoryProtocol",
    "BreedRecordORM",
    "SaleRecordORM",
]
