import logging
from dataclasses import dataclass
from functools import reduce
from typing import Hashable, TypeAlias

import pandas as pd

from ..domain.models import BreedRecord
from ..shared.models import ErrorMessage, ProcessingResult, SourceData
from .processor_interface import IProcessor
from .validator_schema import BreedRecordValidatorSchema
logger = logging.getLogger(__name__)


PreRecords: TypeAlias = tuple[BreedRecord, ...]


@dataclass(frozen=True)
class ProcessState:
    records: tuple[BreedRecord, ...]
    errors: tuple[ErrorMessage, ...]

    def __add__(self, other: "ProcessState") -> "ProcessState":
        return ProcessState(
            records=self.records + other.records,
            errors=self.errors + other.errors,
        )


class BreedsProcessor(IProcessor[BreedRecord]):
    """入雛記錄處理服務"""

    @staticmethod
    def execute(source_data: SourceData) -> ProcessingResult[BreedRecord]:
        """處理資料並返回結果"""

        result = reduce(
            lambda x, y: x + y,
            (
                BreedsProcessor._validate_and_transform_records(row)
                for row in source_data.dataframe.iterrows()
            ),
            ProcessState(records=(), errors=()),
        )

        logger.debug("處理結果: %s", len(result.records))
        logger.debug("處理錯誤: %s", len(result.errors))

        return ProcessingResult(
            source_data=source_data,
            processed_data=list(result.records),
            errors=list(result.errors),
        )

    @staticmethod
    def _validate_and_transform_records(
        row_with_idx: tuple[Hashable, pd.Series],  # type: ignore
    ) -> ProcessState:
        idx, row = row_with_idx
        try:
            validated_record = BreedsProcessor.__transform_records(
                BreedRecordValidatorSchema.model_validate(row)
            )
            return ProcessState(
                records=(validated_record,),
                errors=(),
            )
        except Exception as e:
            return ProcessState(
                records=(),
                errors=(
                    ErrorMessage(
                        message=str(e), data=row.to_dict(), extra={"row_index": idx}
                    ),
                ),
            )

    @staticmethod
    def __transform_records(model: BreedRecordValidatorSchema) -> BreedRecord:
        return BreedRecord(**{
            k: v
            for k, v in model.model_dump().items()
            if k in BreedRecord.__annotations__
        })

    # @staticmethod
    # def _generate_validated_df(df: pd.DataFrame) -> pd.DataFrame:
    #     validated_models: list[BreedRecordValidatorSchema] = []
    #     errors: list[ErrorMessage] = []
    #     for row in df.to_dict(orient="records"):
    #         try:
    #             validated_df_instance = BreedRecordValidatorSchema.model_validate(row)
    #             validated_models.append(validated_df_instance)
    #         except Exception as e:
    #             errors.append(ErrorMessage(message=str(e), data=row.to_dict(), extra={}))
    #     validated_df = pd.DataFrame([model.model_dump() for model in validated_models])
    #     logger.debug("數據內容\n%s", validated_df.head())
    #     logger.debug("數據驗證完成，共 %s 筆資料", len(validated_df))
    #     logger.debug("數據驗證失敗，共 %s 筆資料", len(errors))
    #     logger.debug("驗證數據欄位: %s", list(validated_df.columns))
    #     return validated_df


#     @staticmethod
#     def process_name_cols(df: pd.DataFrame) -> pd.DataFrame:
#         BATCH_GROUP_THRESHOLD = 45
#         """處理名稱相關的列"""
#         try:

#             def calculate_group(group):
#                 group = group.copy().sort_values("breed_date")
#                 group["diff"] = (
#                     group["breed_date"].diff().fillna(pd.Timedelta(seconds=0))
#                 )
#                 group["batch_group"] = (
#                     group["diff"] > pd.Timedelta(days=BATCH_GROUP_THRESHOLD)
#                 ).cumsum() + 1
#                 logger.debug("分組計算完成: %s 筆資料", len(group))
#                 return group

#             def create_location_name(
#                 address: str, origin_location_name: str, name: str
#             ) -> str:
#                 pattern = r"(.{2})(區|鄉)"
#                 match = re.search(pattern, address)
#                 district = match.group(1) if match else ""
#                 result = district + (
#                     name
#                     if origin_location_name == name
#                     else origin_location_name + name
#                 )
#                 logger.debug("場名生成: %s", result)
#                 return result

#             unique_groups = df["farm_name"].unique()
#             result_dfs = [
#                 df[df["farm_name"] == group].groupby("farm_name").apply(calculate_group)
#                 for group in unique_groups
#             ]

#             result_df = pd.concat(result_dfs).reset_index(drop=True)

#             result_df["farmer_name_processed"] = result_df["farmer_name"].str.replace(
#                 "溫福泉|温福泉", "", regex=True
#             )  # type: ignore
#             result_df["farm_name_processed"] = result_df["farm_name"].str.replace(
#                 "畜牧場|牧場", "", regex=True
#             )  # type: ignore
#             result_df["p_location_name"] = result_df.apply(
#                 lambda row: create_location_name(
#                     row["address"],
#                     row["farm_name_processed"],
#                     row["farmer_name_processed"],
#                 ),
#                 axis=1,
#             )

#             logger.debug("名稱處理完成，共 %s 筆資料", len(result_df))
#             return result_df.copy()

#         except Exception as e:
#             logger.error("處理名稱列時發生錯誤: %s", str(e))
#             raise ValueError(f"處理名稱列失敗: {str(e)}") from e

#     @staticmethod
#     def process_group_columns(df: pd.DataFrame) -> pd.DataFrame:
#         """
#         處理分組相關的列並生成入雛代號。

#         處理邏輯：
#         1. 生成批次分組字典
#         2. 映射批次信息
#         3. 生成入雛代號：
#            - 如果存在場別欄位且值不為空，直接使用場別值
#            - 否則使用場名+批次日期格式生成代號

#         Args:
#             df (pd.DataFrame): 包含必要欄位的DataFrame

#         Returns:
#             pd.DataFrame: 處理後的DataFrame，包含入雛代號

#         Raises:
#             ValueError: 處理過程中的錯誤
#         """
#         try:

#             def generate_group_dict(df: pd.DataFrame) -> dict:
#                 dict_pivot = df.pivot_table(
#                     index="batch_group",
#                     columns="p_location_name",
#                     values="breed_date",
#                     aggfunc="median",
#                 )
#                 return dict_pivot.to_dict()

#             def map_group_dict(row: pd.Series, group_dict: dict) -> str:
#                 field = row["p_location_name"]
#                 subgroup = row["batch_group"]
#                 return (
#                     group_dict[field][subgroup]
#                     if field in group_dict and subgroup in group_dict[field]
#                     else None
#                 )  # type: ignore

#             def format_date_and_merge_name(row: pd.Series) -> str:
#                 return row["p_location_name"] + row["batch"].strftime("%y%m")  # type: ignore

#             group_dict = generate_group_dict(df)
#             df["batch"] = df.apply(lambda row: map_group_dict(row, group_dict), axis=1)

#             # 修改這部分：根據場別欄位決定入雛代號
#             mask = ("o_batch_name" in df.columns) & (df["o_batch_name"].notna())
#             df.loc[mask, "batch_name"] = df.loc[mask, "o_batch_name"]
#             df.loc[~mask, "batch_name"] = df.loc[~mask].apply(
#                 format_date_and_merge_name, axis=1
#             )

#             logger.debug("分組處理完成，共 %s 筆資料", len(df))
#             return df

#         except Exception as e:
#             logger.error("處理分組列時發生錯誤: %s", str(e))
#             raise ValueError(f"處理分組列失敗: {str(e)}") from e


# # class BreedRecordRawDataImporter(
# #     IRawDataValidatorService[BreedRecordCreateDto]
# # ):
# #     def __init__(self) -> None:
# #         self._validator = BreedRecordValidatorSchema
# #         self._validated_df: pd.DataFrame | None = None
# #         self._errors: list[ErrorMessage] = []

# #     def validate(self, data: pd.DataFrame) -> bool:
# #         required_columns = list(
# #             self._validator.model_json_schema(by_alias=True)["required"]
# #         )
# #         logger.debug(required_columns)
# #         if not all(col in data.columns for col in required_columns):
# #             raise ValueError("缺少必要欄位")

# #         # validated_df = self._generate_validated_df(data)
# #         return True

# #     def transform(self, raw_data: pd.DataFrame) -> list[BreedRecordCreateDto]:
# #         validated_df = self._generate_validated_df(raw_data)
# #         batch_df = validated_df.pipe(
# #             self.process_name_cols
# #         ).pipe(
# #             self.process_group_columns
# #         )

# #         api_models = [
# #             BreedRecordCreateDto.model_validate(row, from_attributes=True)
# #             for _, row in batch_df.iterrows()
# #         ]
# #         return api_models

# #     def get_errors(self) -> list[ErrorMessage]:
# #         return self._errors
