import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from cleansales_refactor.core.event_bus import TelegramNotifier

from .core.events import ProcessEvent
from .routers import query, upload

# 設定根 logger
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

# 設定特定的 processor logger
processor_logger = logging.getLogger("cleansales_refactor.processor")
processor_logger.setLevel(logging.DEBUG)
# 確保 handler 也設定正確的層級
for handler in processor_logger.handlers:
    handler.setLevel(logging.DEBUG)

# API logger
logger = logging.getLogger(__name__)

# 初始化依賴項
# db = Database("data/cleansales.db")


# def get_event_bus() -> EventBus:
#     return EventBus()


# event_bus = get_event_bus()

telegram_notifier = TelegramNotifier(
    [
        ProcessEvent.SALES_PROCESSING_STARTED,
        ProcessEvent.SALES_PROCESSING_COMPLETED,
        ProcessEvent.SALES_PROCESSING_FAILED,
        ProcessEvent.BREEDS_PROCESSING_STARTED,
        ProcessEvent.BREEDS_PROCESSING_COMPLETED,
        ProcessEvent.BREEDS_PROCESSING_FAILED,
    ],
)


# def get_session() -> Generator[Session, None, None]:
#     with db.get_session() as session:
#         yield session


# def get_api_dependency(
#     event_bus: EventBus = Depends(get_event_bus),
#     session: Session = Depends(get_session),
# ) -> PostApiDependency:
#     return PostApiDependency(event_bus=event_bus, session=session)


# 建立 FastAPI 應用程式
app = FastAPI(
    title="銷售資料處理 API",
    description="""
    提供銷售資料處理服務的 API
    
    ## 功能
    - 上傳 Excel 檔案進行處理
    - 支援 .xlsx 和 .xls 格式
    - 返回處理結果和錯誤訊息
    
    ## 使用方式
    1. 使用 POST `/process-sales` 上傳 Excel 檔案
    2. 系統會自動處理檔案並返回結果
    """,
    version="1.0.0",
)

# 設定靜態檔案目錄
static_path = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# 設定 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> FileResponse:
    return FileResponse(str(static_path / "index.html"))


# 註冊路由
app.include_router(upload.router)
app.include_router(query.router)
