# import logging
# from datetime import date
# from enum import Enum
# from pathlib import Path
# from typing import Any, List, Optional

# import pandas as pd
# from pydantic import BaseModel
# from sqlmodel import Session, SQLModel, and_, asc, or_, select

# from cleansales_refactor import (
#     CleanSalesService,
#     Database,
#     SourceData,
#     ProcessingEvent,
# )
# from cleansales_refactor.exporters import BreedRecordORM
# from event_bus import Event, EventBus, TelegramNotifier
# from fastapi import FastAPI, HTTPException, UploadFile
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import FileResponse
# from fastapi.staticfiles import StaticFiles

# # 先設定基本的 logging 配置
# logging.basicConfig(
#     level=logging.DEBUG,
#     format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
#     handlers=[logging.StreamHandler()],
# )

# # 設定特定的 processor logger
# processor_logger = logging.getLogger("cleansales_refactor.processor")
# processor_logger.setLevel(logging.DEBUG)
# # 確保 handler 也設定正確的層級
# for handler in processor_logger.handlers:
#     handler.setLevel(logging.DEBUG)

# # API logger
# logger = logging.getLogger(__name__)


# class ProcessEvent(Enum):
#     SALES_PROCESSING_STARTED = "sales_processing_started"
#     SALES_PROCESSING_COMPLETED = "sales_processing_completed"
#     SALES_PROCESSING_FAILED = "sales_processing_failed"

#     BREEDS_PROCESSING_STARTED = "breeds_processing_started"
#     BREEDS_PROCESSING_COMPLETED = "breeds_processing_completed"
#     BREEDS_PROCESSING_FAILED = "breeds_processing_failed"


# class ResponseModel(SQLModel):
#     status: str
#     msg: str
#     content: dict[str, Any]


# class SubCardInfo(BaseModel):
#     breed_date: date
#     supplier: Optional[str]
#     male: int
#     female: int


# class BreedCardModel(BaseModel):
#     batch_name: str
#     farm_name: Optional[str]
#     address: Optional[str]
#     farmer_name: Optional[str]
#     chicken_breed: str
#     total_male: int
#     total_female: int
#     veterinarian: Optional[str]
#     is_completed: Optional[str]
#     supplier: Optional[str]  # 只有單筆記錄時使用
#     breed_date: Optional[date]  # 只有單筆記錄時使用
#     sub_cards: List[SubCardInfo] = []  # 多筆記錄時使用


# class BreedSectionModel(BaseModel):
#     breed_type: str
#     total_batches: int
#     total_male: int
#     total_female: int
#     cards: List[BreedCardModel]


# class BreedResponseModel(BaseModel):
#     total_batches: int
#     total_male: int
#     total_female: int
#     sections: List[BreedSectionModel]


# class PostApiDependency:
#     def __init__(self, event_bus: EventBus) -> None:
#         self.service = CleanSalesService()
#         self.event_bus = event_bus

#     def sales_processpipline(
#         self, upload_file: UploadFile, session: Session
#     ) -> ResponseModel:
#         source_data = SourceData(
#             file_name=upload_file.filename or "",
#             dataframe=pd.read_excel(upload_file.file),
#         )
#         result = self.service.execute_clean_sales(session, source_data)
#         if result.status == "success":
#             self.event_bus.publish(
#                 Event(
#                     event=ProcessEvent.SALES_PROCESSING_COMPLETED,
#                     content={"msg": result.msg},
#                 )
#             )
#         return ResponseModel(
#             status=result.status,
#             msg=result.msg,
#             content=result.content,
#         )

#     def breed_processpipline(
#         self, upload_file: UploadFile, session: Session
#     ) -> ResponseModel:
#         source_data = SourceData(
#             file_name=upload_file.filename or "",
#             dataframe=pd.read_excel(upload_file.file),
#         )
#         result = self.service.execute_clean_breeds(session, source_data)
#         if result.status == "success":
#             self.event_bus.publish(
#                 Event(
#                     event=ProcessEvent.BREEDS_PROCESSING_COMPLETED,
#                     content={"msg": result.msg},
#                 )
#             )
#         return ResponseModel(
#             status=result.status,
#             msg=result.msg,
#             content=result.content,
#         )

#     def process_breed_records(
#         self, records: List[BreedRecordORM]
#     ) -> BreedResponseModel:
#         # 依批次分組
#         batch_groups: dict[str, List[BreedRecordORM]] = {}
#         for record in records:
#             batch_name = record.batch_name or "未命名批次"
#             if batch_name not in batch_groups:
#                 batch_groups[batch_name] = []
#             batch_groups[batch_name].append(record)

#         # 處理每個批次的資料
#         all_cards = []
#         for batch_name, batch_records in batch_groups.items():
#             first_record = batch_records[0]

#             if len(batch_records) == 1:
#                 # 單筆記錄
#                 card = BreedCardModel(
#                     batch_name=batch_name,
#                     farm_name=first_record.farm_name,
#                     address=first_record.address,
#                     farmer_name=first_record.farmer_name,
#                     chicken_breed=first_record.chicken_breed or "未分類",
#                     total_male=first_record.male or 0,
#                     total_female=first_record.female or 0,
#                     veterinarian=first_record.veterinarian,
#                     is_completed=first_record.is_completed,
#                     breed_date=first_record.breed_date,
#                     supplier=first_record.supplier,
#                     sub_cards=[],
#                 )
#             else:
#                 # 多筆記錄
#                 card = BreedCardModel(
#                     batch_name=batch_name,
#                     farm_name=first_record.farm_name,
#                     address=first_record.address,
#                     farmer_name=first_record.farmer_name,
#                     chicken_breed=first_record.chicken_breed or "未分類",
#                     total_male=sum(r.male or 0 for r in batch_records),
#                     total_female=sum(r.female or 0 for r in batch_records),
#                     veterinarian=first_record.veterinarian,
#                     is_completed=first_record.is_completed,
#                     breed_date=None,
#                     supplier=None,
#                     sub_cards=[
#                         SubCardInfo(
#                             breed_date=r.breed_date,
#                             supplier=r.supplier,
#                             male=r.male or 0,
#                             female=r.female or 0,
#                         )
#                         for r in batch_records
#                     ],
#                 )
#             all_cards.append(card)

#         # 依品種分組
#         breed_sections: dict[str, List[BreedCardModel]] = {}
#         for card in all_cards:
#             breed_type = card.chicken_breed
#             if breed_type not in breed_sections:
#                 breed_sections[breed_type] = []
#             breed_sections[breed_type].append(card)

#         # 建立最終回應
#         sections = []
#         total_male = 0
#         total_female = 0
#         total_batches = len(all_cards)

#         for breed_type, cards in breed_sections.items():
#             section_total_male = sum(card.total_male for card in cards)
#             section_total_female = sum(card.total_female for card in cards)
#             total_male += section_total_male
#             total_female += section_total_female

#             sections.append(
#                 BreedSectionModel(
#                     breed_type=breed_type,
#                     total_batches=len(cards),
#                     total_male=section_total_male,
#                     total_female=section_total_female,
#                     cards=cards,
#                 )
#             )

#         return BreedResponseModel(
#             total_batches=total_batches,
#             total_male=total_male,
#             total_female=total_female,
#             sections=sorted(sections, key=lambda x: x.breed_type),
#         )

#     def get_breeds_is_not_completed(self, session: Session) -> ResponseModel:
#         stmt = (
#             select(BreedRecordORM)
#             .where(
#                 and_(
#                     or_(
#                         BreedRecordORM.is_completed != "結場",
#                         BreedRecordORM.is_completed == None,
#                     ),
#                     BreedRecordORM.event == ProcessingEvent.ADDED,
#                 )
#             )
#             .order_by(asc(BreedRecordORM.breed_date))
#         )
#         breeds = session.exec(stmt).all()

#         breed_data = self.process_breed_records(list(breeds))

#         return ResponseModel(
#             status="success",
#             msg=f"成功取得未結場入雛資料 {len(breeds)} 筆",
#             content=breed_data.model_dump(),
#         )


# db = Database("data/cleansales.db")
# event_bus = EventBus()
# telegram_notifier = TelegramNotifier(
#     event_bus,
#     [
#         ProcessEvent.SALES_PROCESSING_STARTED,
#         ProcessEvent.SALES_PROCESSING_COMPLETED,
#         ProcessEvent.SALES_PROCESSING_FAILED,
#         ProcessEvent.BREEDS_PROCESSING_STARTED,
#         ProcessEvent.BREEDS_PROCESSING_COMPLETED,
#         ProcessEvent.BREEDS_PROCESSING_FAILED,
#     ],
# )
# api_function = PostApiDependency(event_bus)

# app = FastAPI(
#     title="銷售資料處理 API",
#     description="""
#     提供銷售資料處理服務的 API
    
#     ## 功能
#     - 上傳 Excel 檔案進行處理
#     - 支援 .xlsx 和 .xls 格式
#     - 返回處理結果和錯誤訊息
    
#     ## 使用方式
#     1. 使用 POST `/process-sales` 上傳 Excel 檔案
#     2. 系統會自動處理檔案並返回結果
#     """,
#     version="1.0.0",
# )

# # 設定靜態檔案目錄
# static_path = Path(__file__).parent / "static"
# app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# # 設定 CORS
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# @app.get("/")
# async def root() -> FileResponse:
#     return FileResponse(str(static_path / "index.html"))


# @app.post("/process-sales", response_model=ResponseModel)
# async def process_sales_file(
#     file_upload: UploadFile,
# ) -> ResponseModel:
#     """處理上傳的銷售資料檔案

#     Args:
#         file_upload: 包含上傳的 Excel 檔案的 Pydantic 模型

#     Returns:
#         包含處理結果的字典

#     Raises:
#         HTTPException: 當檔案格式不正確或處理過程發生錯誤時
#     """
#     with db.get_session() as session:
#         try:
#             # 讀取檔案內容
#             if file_upload.filename is None:
#                 raise ValueError("未提供檔案名稱")
#             if not file_upload.filename.endswith((".xlsx", ".xls")):
#                 raise ValueError("只接受 Excel 檔案 (.xlsx, .xls)")
#             # 處理檔案
#             result: ResponseModel = api_function.sales_processpipline(
#                 file_upload, session
#             )
#             return result
#         except ValueError as ve:
#             raise HTTPException(status_code=400, detail=str(ve))
#         except Exception as e:
#             logger.error(f"處理販售資料檔案時發生錯誤: {e}")
#             event_bus.publish(
#                 Event(
#                     event=ProcessEvent.SALES_PROCESSING_FAILED,
#                     content={
#                         "msg": str(e),
#                     },
#                 )
#             )
#             raise HTTPException(status_code=500, detail=str(e))


# @app.post("/process-breeds", response_model=ResponseModel)
# async def process_breeds_file(
#     file_upload: UploadFile,
# ) -> ResponseModel:
#     with db.get_session() as session:
#         try:
#             if file_upload.filename is None:
#                 raise ValueError("未提供檔案名稱")
#             if not file_upload.filename.endswith((".xlsx", ".xls")):
#                 raise ValueError("只接受 Excel 檔案 (.xlsx, .xls)")
#             result: ResponseModel = api_function.breed_processpipline(
#                 file_upload, session
#             )
#             return result
#         except ValueError as ve:
#             raise HTTPException(status_code=400, detail=str(ve))
#         except Exception as e:
#             logger.error(f"處理入雛資料檔案時發生錯誤: {e}")
#             event_bus.publish(
#                 Event(
#                     event=ProcessEvent.BREEDS_PROCESSING_FAILED,
#                     content={
#                         "msg": str(e),
#                     },
#                 )
#             )
#             raise HTTPException(status_code=500, detail=str(e))


# @app.post("/test_notification")
# async def test_notification(
#     msg: str,
# ) -> ResponseModel:
#     event_bus.publish(
#         Event(
#             event=ProcessEvent.SALES_PROCESSING_COMPLETED,
#             content={"msg": msg},
#         )
#     )
#     return ResponseModel(status="success", msg="測試通知成功", content={})


# @app.get("/breeding", response_model=ResponseModel)
# async def get_breeding_data() -> ResponseModel:
#     with db.get_session() as session:
#         try:
#             return api_function.get_breeds_is_not_completed(session)
#         except Exception as e:
#             logger.error(f"取得未結場入雛資料時發生錯誤: {e}")
#             raise HTTPException(status_code=500, detail=str(e))


# if __name__ == "__main__":
#     import uvicorn

#     uvicorn.run(
#         "api:app",
#         host="0.0.0.0",
#         port=8000,
#         reload=True,
#         reload_dirs=["src"],
#     )
