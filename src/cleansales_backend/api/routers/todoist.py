import json
import logging
import re
from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field, field_validator
from todoist_api_python.api import TodoistAPI
from todoist_api_python.models import Item, Task

from cleansales_backend.core import get_settings

# 配置查詢路由器專用的日誌記錄器
logger = logging.getLogger(__name__)


class GetTasksRequest(BaseModel):
    project_id: str | None = None
    section_id: str | None = None
    label: str | None = None
    filter: str | None = None
    lang: str | None = None
    ids: list[str] | None = None


class GetCompletedItemsRequest(BaseModel):
    project_id: str | None = None
    section_id: str | None = None
    item_id: str | None = None
    last_seen_id: str | None = None
    limit: int | None = None
    cursor: str | None = None


# Pydantic 請求模型
class CreateTaskRequest(BaseModel):
    content: str
    description: str | None = None
    project_id: str | int | None = None
    section_id: str | int | None = None
    parent_id: str | int | None = None
    order: int | None = Field(None, ge=0)
    labels: list[str] | None = None
    priority: int | None = Field(None, ge=1, le=4)
    due_string: str | None = None
    due_datetime: str | None = None  # RFC3339
    due_lang: str | None = None
    assignee_id: str | None = None
    duration: int | None = Field(None, ge=0)
    duration_unit: str | None = None
    deadline: str | None = None
    deadline_lang: str | None = None

    @field_validator("deadline", mode="before")
    @classmethod
    def validate_deadline(cls, v: str | None) -> str | None:
        # 驗證格式是否為YYYY-MM-DD
        if v is None:
            return None
        else:
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
                raise ValueError("deadline must be in the format YYYY-MM-DD")
            return v


class TaskActionRequest(BaseModel):
    task_id: str


class TodoistUtils:
    @classmethod
    def get_project_id_by_name(cls, api: TodoistAPI, project_name: str) -> str:
        projects = api.get_projects()
        logger.info(f"專案列表: {projects}")
        if not projects:
            raise ValueError("No projects found")
        result = next((p.id for p in projects if p.name == project_name), None)
        if result is None:
            raise ValueError(f"Project '{project_name}' not found")
        return result

    @classmethod
    def item_to_task(cls, item: Item) -> Task:
        return Task(
            # 共同字段
            id=item.id,
            content=item.content,
            description=item.description,
            priority=item.priority,
            project_id=item.project_id,
            section_id=item.section_id,
            due=item.due,
            sync_id=item.sync_id,
            labels=item.labels,
            # 特殊映射
            is_completed=item.checked,
            parent_id=str(item.parent_id) if item.parent_id else None,
            # Task 特殊字段
            assigner_id=item.assigned_by_uid,
            assignee_id=item.responsible_uid,
            comment_count=0,
            created_at=item.added_at,
            creator_id=item.user_id or item.added_by_uid or "",
            order=item.child_order,
            url="",
            duration=None,
        )


@lru_cache(maxsize=1)
def get_todoist_api() -> TodoistAPI:
    token = get_settings().TODOIST_API_TOKEN
    if not token:
        raise ValueError("請在 .env 檔中設定 TODOIST_API_TOKEN")
    return TodoistAPI(token)


router = APIRouter(prefix="/api/todoist", tags=["todoist"])


@router.get("/p/{project_name}/id")
async def get_project_id_by_name(
    project_name: str,
    api: TodoistAPI = Depends(get_todoist_api),
) -> Response:
    try:
        project_id = TodoistUtils.get_project_id_by_name(api, project_name)
        return Response(content=project_id, media_type="application/json")
    except ValueError as e:
        logger.error(f"找不到專案 ID: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"API 發生錯誤: {e}")
        raise HTTPException(
            status_code=500, detail={"error": str(e), "type": type(e).__name__}
        )


@router.get("/tasks")
async def get_tasks(
    request: GetTasksRequest = Query(...),
    api: TodoistAPI = Depends(get_todoist_api),
) -> Response:
    try:
        tasks = api.get_tasks(**request.model_dump(exclude_none=True))
        logger.info(tasks)
        return Response(
            content=json.dumps([task.to_dict() for task in tasks]),
            media_type="application/json",
        )
    except ValueError as e:
        logger.error(f"找不到專案 ID: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"API發生錯誤: {e}")
        raise HTTPException(
            status_code=500, detail={"error": str(e), "type": type(e).__name__}
        )


@router.get("/completed")
async def get_completed_tasks(
    project_id: str,
    label: str | None = None,
    api: TodoistAPI = Depends(get_todoist_api),
) -> Response:
    try:
        completed_items = api.get_completed_items(project_id=project_id)
        items = [
            item
            for item in completed_items.items
            if label in item.labels or label is None
        ]
        # logger.info(items)
        while completed_items.has_more:
            completed_items = api.get_completed_items(
                project_id=project_id, cursor=completed_items.next_cursor
            )
            items.extend(
                [
                    item
                    for item in completed_items.items
                    if label in item.labels or label is None
                ]
            )
        tasks = [TodoistUtils.item_to_task(item) for item in items]
        # logger.info(tasks)
        return Response(
            content=json.dumps([task.to_dict() for task in tasks]),
            media_type="application/json",
        )
    except Exception as e:
        logger.error(f"獲取完成項目時發生錯誤: {e}")
        raise HTTPException(
            status_code=500, detail={"error": str(e), "type": type(e).__name__}
        )


@router.post("/create_task")
async def create_task(
    task: CreateTaskRequest, api: TodoistAPI = Depends(get_todoist_api)
) -> Response:
    try:
        # 處理請求數據
        task_data = task.model_dump(exclude_unset=True)
        created_task = api.add_task(**task_data)
        return Response(
            content=json.dumps(created_task.to_dict()), media_type="application/json"
        )
    except Exception as e:
        logger.error(f"創建任務時發生錯誤: {e}")
        raise HTTPException(
            status_code=500, detail={"error": str(e), "type": type(e).__name__}
        )


@router.post("/close_task/{task_id}")
async def close_task(
    task_id: str, api: TodoistAPI = Depends(get_todoist_api)
) -> Response:
    try:
        result = api.close_task(task_id=task_id)
        return Response(
            content=json.dumps({"success": result}), media_type="application/json"
        )
    except Exception as e:
        logger.error(f"完成任務時發生錯誤: {e}")
        raise HTTPException(
            status_code=500, detail={"error": str(e), "type": type(e).__name__}
        )


@router.post("/reopen_task/{task_id}")
async def reopen_task(
    task_id: str, api: TodoistAPI = Depends(get_todoist_api)
) -> Response:
    try:
        result = api.reopen_task(task_id=task_id)
        return Response(
            content=json.dumps({"success": result}), media_type="application/json"
        )
    except Exception as e:
        logger.error(f"重新開啟任務時發生錯誤: {e}")
        raise HTTPException(
            status_code=500, detail={"error": str(e), "type": type(e).__name__}
        )


@router.post("/delete_task/{task_id}")
async def delete_task(
    task_id: str, api: TodoistAPI = Depends(get_todoist_api)
) -> Response:
    try:
        result = api.delete_task(task_id=task_id)
        return Response(
            content=json.dumps({"success": result}), media_type="application/json"
        )
    except Exception as e:
        logger.error(f"刪除任務時發生錯誤: {e}")
        raise HTTPException(
            status_code=500, detail={"error": str(e), "type": type(e).__name__}
        )
