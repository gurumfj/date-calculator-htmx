# from .breeds_processor import BreedsProcessor
from .breeds_schema import BreedRecordProcessor
from .interface.breed_repository_protocol import BreedRepositoryProtocol
from .interface.processors_interface import IBaseModel, IORMModel, IProcessor, IResponse
from .interface.sale_repository_protocol import SaleRepositoryProtocol
from .sales_schema import SaleRecordProcessor

__all__ = [
    "IProcessor",
    "BreedRecordProcessor",
    "SaleRecordProcessor",
    "IBaseModel",
    "IORMModel",
    "IResponse",
    "BreedRepositoryProtocol",
    "SaleRepositoryProtocol",
]
