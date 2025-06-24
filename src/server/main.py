import logging
import os
import secrets

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware

from db_init import init_db
from server.api_route import router as api_router
from server.batches_route import router as batches_router
from server.date_calculator_route import router as date_calculator_router
from server.sales_route import router as sales_router
from server.upload_route import router as upload_router

logger = logging.getLogger(__name__)

# Initialize database
init_db()

# Create main application
app = FastAPI(title="CleanSales Management System")


# Security Headers Middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # CSP removed for local development - will be added for remote deployment
        
        return response

# Add session middleware for date calculator
# Use environment variable or generate secure random key
session_secret = os.getenv("SESSION_SECRET_KEY")
if not session_secret:
    session_secret = secrets.token_urlsafe(32)
    logger.warning("SESSION_SECRET_KEY not set, using randomly generated key. This will invalidate sessions on restart.")

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(
    SessionMiddleware,
    secret_key=session_secret,
)

# CSRF protection removed for local development - will be added with other tools for production

# Setup Jinja2 templates
templates = Jinja2Templates(directory="src/server/templates")

# Setup static files
app.mount("/static", StaticFiles(directory="src/server/static"), name="static")

# Main system navigation
MAIN_NAV_ITEMS = [
    {"title": "Data Uploader", "value": "uploader", "href": "/uploader"},
    {"title": "Date Calculator", "value": "date_calculator", "href": "/date_calculator"},
    {"title": "Sales Records", "value": "sales", "href": "/sales"},
    {"title": "Batches", "value": "batches", "href": "/batches"},
    # Future: Add other systems here
    # {"title": "Analytics", "value": "analytics", "href": "/analytics"},
    # {"title": "Reports", "value": "reports", "href": "/reports"},
]


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """主頁面 - 系統導航選單"""
    return templates.TemplateResponse("index.html", {"request": request, "nav_items": MAIN_NAV_ITEMS})


# Include routers
app.include_router(upload_router, prefix="/uploader", tags=["uploader"])
app.include_router(api_router, prefix="/api", tags=["api"])
app.include_router(date_calculator_router, prefix="/date_calculator", tags=["date_calculator"])
app.include_router(sales_router, prefix="/sales", tags=["sales"])
app.include_router(batches_router, prefix="/batches", tags=["batches"])


# Legacy compatibility routes - redirect to uploader
@app.get("/upload", response_class=HTMLResponse)
@app.get("/events", response_class=HTMLResponse)
@app.get("/breeds", response_class=HTMLResponse)
@app.get("/feeds", response_class=HTMLResponse)
@app.get("/farm_production", response_class=HTMLResponse)
@app.get("/sql", response_class=HTMLResponse)
async def legacy_redirect(request: Request):
    """向後兼容 - 重定向到 uploader"""
    path = request.url.path
    return RedirectResponse(url=f"/uploader{path}", status_code=302)


# Legacy API compatibility - redirect to new API route
# Note: /api/upload now handled by api_router, no redirect needed


# def init_todoist():
#     if not get_settings().TODOIST_API_TOKEN:
#         raise ValueError("TODOIST_API_TOKEN is not set")
#     return TodoistAPI(token=get_settings().TODOIST_API_TOKEN)


# @app.get("/todoist", response_class=HTMLResponse)
# async def todoist(request: Request):
#     """向後兼容 - 重定向到 uploader"""
#     todoist = init_todoist()
#     # tasks = todoist.get_tasks()
#     # tasks = [task.to_dict() for task_list in tasks for task in task_list]
#     params_lst: list[tuple[datetime, datetime]] = []
#     # 以4週為單位, 創造近3年的時間區間
#     since = datetime.now() - timedelta(years=3)
#     for i in range(3):
#         params_since = since + timedelta(weeks=i*4)
#         params_lst.append((params_since, since + timedelta(weeks=(i+1)*4)))
#     tasks: list[Task] = []
#     for params in params_lst:
#         completed_tasks = todoist.get_completed_tasks_by_due_date(since=params[0], until=params[1])
#         tasks.extend([task.to_dict() for task_list in completed_tasks for task in task_list])
#     tasks = [task.to_dict() for task_list in completed_tasks for task in task_list]

#     return templates.TemplateResponse("todoist.html", {"request": request, "now": datetime.now(), "tasks": tasks})


def main() -> None:
    import uvicorn

    uvicorn.run("server.main:app", host="0.0.0.0", port=8000, reload=True, forwarded_allow_ips="*")


if __name__ == "__main__":
    main()
