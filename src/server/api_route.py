import json
import logging

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse

from cleansales_backend.commands.upload_commands import UploadFileCommand
from cleansales_backend.database.init import init_db
from cleansales_backend.handlers.upload_handler import UploadCommandHandler

logger = logging.getLogger(__name__)
DB_PATH = "./data/sqlite.db"

init_db()

# Create API router
router = APIRouter()

upload_handler = UploadCommandHandler(DB_PATH)


@router.post("/upload")
async def api_upload(file: UploadFile = File(...)):
    """API上傳路由，返回JSON格式"""
    command = UploadFileCommand(file=file)
    result = await upload_handler.handle(command)

    # 使用 UploadResult 的 to_json 方法
    return JSONResponse(content=json.loads(result.to_json(ensure_ascii=False)))


# This router will be included in main.py