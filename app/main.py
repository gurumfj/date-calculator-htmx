import logging
import os
from datetime import datetime

from fastapi import FastAPI, Form, Request
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from starlette.middleware.sessions import SessionMiddleware

from .models import DateData, DateInterval
from .session import get_session_store, save_to_session

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get configuration from environment variables
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# Create FastAPI app
app = FastAPI(
    title="Date Calculator API",
    description="A simple date calculator with interval and calculation features",
    version="1.0.0",
    debug=DEBUG,
)

# Add compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add session middleware for storing calculations
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def get_date_calculator(request: Request):
    """日期計算機主頁面"""
    store = get_session_store(request)

    context = {"request": request, "store": store, "current_date": datetime.now().date().strftime("%Y-%m-%d")}

    return templates.TemplateResponse("date_calculator/index.html", context)


@app.post("/calculate", response_class=HTMLResponse)
async def calculate_date(
    request: Request,
    base_date: str = Form(...),
    operation: str = Form(...),
    amount: int = Form(...),
    unit: str = Form(...),
    id: str = Form(...),
):
    """執行日期計算"""
    try:
        # 直接從表單輸入創建 DateData
        data = DateData.from_form_input(
            base_date=base_date,
            operation=operation,
            amount=amount,
            unit=unit,
            id=id,
            description="",  # 新計算預設空白
        )

        # Calculate the result
        result = DateData.calculate_date(data)

        # Add to session store (prepend for newest first)
        store = get_session_store(request)
        store.insert(0, result)
        save_to_session(request, store)

        context = {"request": request, "date_data": result}

        return templates.TemplateResponse("date_calculator/result_card.html", context)

    except (ValueError, ValidationError):
        return HTMLResponse(content='<div style="color: red;">計算錯誤: 輸入格式不正確</div>', status_code=400)


@app.post("/pickup", response_class=HTMLResponse)
async def pickup_date(
    request: Request,
    base_date: str = Form(...),
    operation: str = Form(...),
    amount: int = Form(...),
    unit: str = Form(...),
    id: str = Form(...),
):
    """拾取日期到表單"""
    try:
        # 直接從表單輸入創建 DateData
        data = DateData.from_form_input(
            base_date=base_date,
            operation=operation,
            amount=amount,
            unit=unit,
            id=id,
            description="",  # pickup 時不包含描述
        )

        context = {"request": request, "data": data}

        return templates.TemplateResponse("date_calculator/form_content.html", context)

    except (ValueError, ValidationError):
        return HTMLResponse(content='<div style="color: red;">格式錯誤: 輸入格式不正確</div>', status_code=400)


@app.post("/calculate_interval", response_class=HTMLResponse)
async def calculate_interval(request: Request, start_date: str = Form(...), end_date: str = Form(...)):
    """計算兩個日期之間的間隔"""
    try:
        # 直接從表單輸入創建 DateInterval
        result = DateInterval.from_form_input(
            start_date=start_date,
            end_date=end_date,
            description="",  # 新計算預設空白
        )

        # Add to session store (prepend for newest first)
        store = get_session_store(request)
        store.insert(0, result)
        save_to_session(request, store)

        context = {"request": request, "interval_data": result}

        return templates.TemplateResponse("date_calculator/interval_result_card.html", context)

    except (ValueError, ValidationError):
        return HTMLResponse(content='<div style="color: red;">計算錯誤: 輸入格式不正確</div>', status_code=400)


@app.delete("/delete/all", response_class=HTMLResponse)
async def delete_all_calculations(request: Request):
    """清除所有計算記錄"""
    try:
        save_to_session(request, [])

        return HTMLResponse(content="")
    except Exception as e:
        logger.error(f"Error deleting all calculations: {e}")
        return HTMLResponse(content="", status_code=500)


@app.delete("/delete/{id}", response_class=HTMLResponse)
async def delete_date_calculation(request: Request, id: str):
    """刪除單個計算記錄"""
    try:
        store = get_session_store(request)
        updated_store = [data for data in store if data.id != id]
        save_to_session(request, updated_store)

        return HTMLResponse(content="")
    except Exception as e:
        logger.error(f"Error deleting calculation: {e}")
        return HTMLResponse(content="", status_code=500)


@app.post("/save_description/{id}", response_class=HTMLResponse)
async def save_description(request: Request, id: str, description: str = Form("")):
    """儲存描述"""
    try:
        store = get_session_store(request)

        # 找到並更新描述
        for i, data in enumerate(store):
            if data.id == id:
                # 根據數據類型創建新物件，利用 BaseModel 的驗證
                if isinstance(data, DateData):
                    updated_data = DateData(
                        id=data.id,
                        base_date=data.base_date,
                        operation=data.operation,
                        amount=data.amount,
                        unit=data.unit,
                        result=data.result,
                        description=description,  # 會被 DateData 的 sanitize_description 驗證
                    )
                elif isinstance(data, DateInterval):
                    updated_data = DateInterval(
                        id=data.id,
                        start_date=data.start_date,
                        end_date=data.end_date,
                        days_diff=data.days_diff,
                        description=description,
                    )
                else:
                    continue

                store[i] = updated_data
                save_to_session(request, store)

                # 返回更新後的單個卡片
                context = {
                    "request": request,
                    "date_data": updated_data if isinstance(updated_data, DateData) else None,
                    "interval_data": updated_data if isinstance(updated_data, DateInterval) else None,
                }

                template_name = (
                    "date_calculator/result_card.html"
                    if isinstance(updated_data, DateData)
                    else "date_calculator/interval_result_card.html"
                )
                return templates.TemplateResponse(template_name, context)

        return HTMLResponse(content="error", status_code=404)

    except ValidationError:
        return HTMLResponse(content="error: invalid description", status_code=400)


def main():
    """Entry point for uvicorn development server"""
    import uvicorn

    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=DEBUG, log_level="info" if not DEBUG else "debug")


if __name__ == "__main__":
    main()
