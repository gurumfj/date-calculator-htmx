import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Literal, Optional

from todoist_api_python.api import TodoistAPI
from todoist_api_python.models import Task

from db_init import get_db_connection_context
from server.config import get_settings

logger = logging.getLogger(__name__)

todoist_token = get_settings().TODOIST_API_TOKEN
if not todoist_token:
    raise ValueError("TODOIST_API_TOKEN is not set")
todoist = TodoistAPI(todoist_token)


class TodoistCacheService:
    """Todoist 快取服務，專注於本地 SQLite 快取操作"""

    COMPLETED_TASK_ALIVE_HOURS = 24
    ACTIVE_TASK_ALIVE_HOURS = 1

    def __init__(self):
        pass

    def is_cache_valid_by_type(self, batch_name: str, task_type: Literal["active", "completed"]) -> bool:
        """檢查特定任務類型的快取是否有效（包含空結果快取）"""
        with get_db_connection_context() as conn:
            cutoff_time = datetime.now() - timedelta(
                hours=self.ACTIVE_TASK_ALIVE_HOURS if task_type == "active" else self.COMPLETED_TASK_ALIVE_HOURS
            )
            
            # 檢查 metadata 表中是否有有效的查詢記錄
            row = conn.execute(
                """
                SELECT query_timestamp, task_count FROM todoist_cache_metadata 
                WHERE batch_name = :batch_name AND task_type = :task_type
            """,
                {
                    "batch_name": batch_name,
                    "task_type": task_type,
                },
            ).fetchone()
            
            if not row:
                return False
                
            query_timestamp = datetime.fromisoformat(row[0])
            task_count = row[1]
            
            # 檢查查詢時間是否在有效期內
            if query_timestamp > cutoff_time:
                logger.debug(f"快取有效 - batch: {batch_name}, type: {task_type}, count: {task_count}")
                return True
            
            logger.debug(f"快取過期 - batch: {batch_name}, type: {task_type}, query_time: {query_timestamp}")
            return False

    def get_cached_task_by_id(self, task_id: str) -> Optional[Dict[str, Any]]:
        """從快取取得單個任務"""
        with get_db_connection_context() as conn:
            row = conn.execute(
                """
                SELECT id, batch_name, task_id, task_type, content, description, 
                       due_date, completed_at, labels, priority, created_at, 
                       updated_at, cached_at
                FROM todoist_cache 
                WHERE task_id = :task_id
            """,
                {"task_id": task_id},
            ).fetchone()

            if row:
                task = dict(row)
                if task["labels"]:
                    try:
                        task["labels"] = json.loads(task["labels"])
                    except (json.JSONDecodeError, TypeError):
                        task["labels"] = []
                else:
                    task["labels"] = []
                return task
            return None

    def get_cached_tasks_by_type(
        self, batch_name: str, task_type: Literal["active", "completed"] = "active"
    ) -> List[Dict[str, Any]]:
        """從快取取得任務"""
        with get_db_connection_context() as conn:
            rows = conn.execute(
                """
                SELECT id, batch_name, task_id, task_type, content, description, 
                       due_date, completed_at, labels, priority, created_at, 
                       updated_at, cached_at
                FROM todoist_cache 
                WHERE batch_name = :batch_name AND task_type = :task_type
                ORDER BY task_type, created_at DESC
            """,
                {"batch_name": batch_name, "task_type": task_type},
            ).fetchall()

            tasks = []
            for row in rows:
                task = dict(row)
                # 解析 JSON 欄位
                if task["labels"]:
                    try:
                        task["labels"] = json.loads(task["labels"])
                    except (json.JSONDecodeError, TypeError):
                        task["labels"] = []
                else:
                    task["labels"] = []
                tasks.append(task)

            return tasks

    def save_tasks_to_cache_by_type(
        self, batch_name: str, tasks: list[Task], task_type: Literal["active", "completed"] = "active"
    ):
        """儲存任務到快取，包含空結果記錄"""
        with get_db_connection_context() as conn:
            current_time = datetime.now().isoformat()
            task_count = len(tasks)
            
            # 清除舊快取
            conn.execute(
                "DELETE FROM todoist_cache WHERE batch_name = :batch_name AND task_type = :task_type",
                {"batch_name": batch_name, "task_type": task_type},
            )

            # 儲存任務到快取（如果有的話）
            for task in tasks:
                conn.execute(
                    """
                        INSERT OR REPLACE INTO todoist_cache 
                        (batch_name, task_id, task_type, content, description, due_date, 
                         completed_at, labels, priority, created_at, cached_at)
                        VALUES (:batch_name, :task_id, :task_type, :content, :description, :due_date, 
                         :completed_at, :labels, :priority, :created_at, :cached_at)
                    """,
                    {
                        "batch_name": batch_name,
                        "task_id": task.id,
                        "task_type": task_type,
                        "content": task.content,
                        "description": task.description,
                        "due_date": task.due.date.isoformat() if task.due else None,
                        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                        "labels": json.dumps(task.labels),
                        "priority": task.priority,
                        "created_at": task.created_at.isoformat() if task.created_at else None,
                        "cached_at": current_time,
                    },
                )
            
            # 更新查詢記錄到 metadata 表（無論是否有任務都要記錄）
            conn.execute(
                """
                INSERT OR REPLACE INTO todoist_cache_metadata 
                (batch_name, task_type, query_timestamp, task_count)
                VALUES (:batch_name, :task_type, :query_timestamp, :task_count)
                """,
                {
                    "batch_name": batch_name,
                    "task_type": task_type,
                    "query_timestamp": current_time,
                    "task_count": task_count,
                },
            )
            
            logger.info(f"快取已更新 - batch: {batch_name}, type: {task_type}, count: {task_count}")

    # def clear_expired_cache(self, max_age_hours: int = 24) -> int:
    #     """清理過期快取"""
    #     with get_db_connection_context() as conn:
    #         cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
    #         cursor = conn.execute(
    #             """
    #             DELETE FROM todoist_cache WHERE cached_at < :cutoff_time
    #         """,
    #             {"cutoff_time": cutoff_time.isoformat()},
    #         )
    #         return cursor.rowcount

    def save_task_to_cache(self, batch_name: str, task: Task, task_type: str = "active"):
        """儲存單個任務到快取"""
        with get_db_connection_context() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO todoist_cache 
                (batch_name, task_id, task_type, content, description, due_date, 
                 completed_at, labels, priority, created_at, cached_at)
                VALUES (:batch_name, :task_id, :task_type, :content, :description, :due_date, 
                 :completed_at, :labels, :priority, :created_at, :cached_at)
            """,
                {
                    "batch_name": batch_name,
                    "task_id": task.id,
                    "task_type": task_type,
                    "content": task.content,
                    "description": task.description,
                    "due_date": task.due.date.isoformat() if task.due else None,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                    "labels": json.dumps(task.labels),
                    "priority": task.priority,
                    "created_at": task.created_at.isoformat() if task.created_at else None,
                    "cached_at": datetime.now().isoformat(),
                },
            )

    def delete_task_from_cache(self, task_id: str):
        """從快取刪除任務"""
        with get_db_connection_context() as conn:
            conn.execute(
                """
                DELETE FROM todoist_cache 
                WHERE task_id = :task_id
            """,
                {"task_id": task_id},
            )

    def mark_task_completed_in_cache(self, task_id: str):
        """在快取中標記任務為完成"""
        with get_db_connection_context() as conn:
            now = datetime.now().isoformat()
            conn.execute(
                """
                UPDATE todoist_cache 
                SET task_type = 'completed', 
                    completed_at = :completed_at,
                    updated_at = :updated_at
                WHERE task_id = :task_id
            """,
                {
                    "task_id": task_id,
                    "completed_at": now,
                    "updated_at": now,
                },
            )

    def mark_task_uncompleted_in_cache(self, task_id: str):
        """在快取中標記任務為未完成"""
        with get_db_connection_context() as conn:
            now = datetime.now().isoformat()
            conn.execute(
                """
                UPDATE todoist_cache 
                SET task_type = 'active', 
                    completed_at = NULL,
                    updated_at = :updated_at
                WHERE task_id = :task_id
            """,
                {
                    "task_id": task_id,
                    "updated_at": now,
                },
            )

    def update_task_in_cache(
        self, task_id: str, content: Optional[str] = None, description: Optional[str] = None
    ):
        """更新快取中的任務"""
        with get_db_connection_context() as conn:
            update_fields = []
            params = {
                "task_id": task_id,
                "updated_at": datetime.now().isoformat(),
            }

            if content is not None:
                update_fields.append("content = :content")
                params["content"] = content

            if description is not None:
                update_fields.append("description = :description")
                params["description"] = description

            if update_fields:
                update_fields.append("updated_at = :updated_at")

                conn.execute(
                    f"""
                    UPDATE todoist_cache 
                    SET {", ".join(update_fields)}
                    WHERE task_id = :task_id
                """,
                    params,
                )

    def get_task_from_cache(self, task_id: str) -> Optional[Dict[str, Any]]:
        """從快取獲取單個任務"""
        with get_db_connection_context() as conn:
            row = conn.execute(
                """
                SELECT id, batch_name, task_id, task_type, content, description, 
                       due_date, completed_at, labels, priority, created_at, 
                       updated_at, cached_at
                FROM todoist_cache 
                WHERE task_id = :task_id
            """,
                {
                    "task_id": task_id,
                },
            ).fetchone()

            if row:
                task = dict(row)
                if task["labels"]:
                    try:
                        task["labels"] = json.loads(task["labels"])
                    except (json.JSONDecodeError, TypeError):
                        task["labels"] = []
                else:
                    task["labels"] = []
                return task
            return None


class TodoService:
    def __init__(self, todoist_api: TodoistAPI, cache_service: TodoistCacheService):
        self.todoist = todoist_api
        self.cache = cache_service

    def _get_tasks_by_label(self, label: str):
        tasks_iter = self.todoist.get_tasks(label=label)
        tasks: list[Task] = []
        for task_list in tasks_iter:
            tasks.extend(task_list)
        return tasks

    def _get_completed_tasks_by_due_date(self, since: datetime, until: datetime, label: str | None = None):
        # 如果since and until 相差 4weeks, 將params拆分為多個請求
        params_lst: list[tuple[datetime, datetime]] = []
        task_count = (until - since).days // 28 + 1
        next_since = since
        for _ in range(task_count):
            params_lst.append((next_since, next_since + timedelta(weeks=4)))
            next_since += timedelta(weeks=4)

        tasks: list[Task] = []
        for params in params_lst:
            completed_tasks = self.todoist.get_completed_tasks_by_due_date(
                since=params[0], until=params[1], filter_query=f"@{label}" if label else None
            )
            tasks.extend([task for task_list in completed_tasks for task in task_list])
        return tasks

    def get_active_tasks_with_cache(self, batch_name: str, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """帶快取的活動任務查詢 - 快速響應，短期快取"""
        try:
            # 檢查活動任務快取是否有效（30分鐘）
            if not force_refresh and self.cache.is_cache_valid_by_type(batch_name, "active"):
                logger.info(f"使用活動任務快取數據: {batch_name}")
                return self.cache.get_cached_tasks_by_type(batch_name, "active")

            # 快取失效，從 API 獲取活動任務
            logger.info(f"從 API 獲取活動任務: {batch_name}")
            active_tasks = self._get_tasks_by_label(batch_name)

            # 儲存到快取
            self.cache.save_tasks_to_cache_by_type(batch_name, active_tasks, "active")

            # 回傳快取中的活動任務
            return self.cache.get_cached_tasks_by_type(batch_name, "active")

        except Exception as e:
            logger.error(f"獲取活動任務失敗: {e}")
            # 如果 API 失敗，嘗試返回快取數據（即使可能過期）
            try:
                cached_tasks = self.cache.get_cached_tasks_by_type(batch_name, "active")
                if cached_tasks:
                    logger.warning(f"API 失敗，使用過期活動任務快取: {batch_name}")
                    return cached_tasks
            except Exception:
                pass
            raise

    def get_completed_tasks_with_cache(
        self, batch_name: str, since: datetime, until: datetime, force_refresh: bool = False
    ) -> List[Dict[str, Any]]:
        """帶快取的已完成任務查詢 - 長期快取，較少更新"""
        try:
            # 檢查已完成任務快取是否有效（4小時）
            if not force_refresh and self.cache.is_cache_valid_by_type(batch_name, "completed"):
                logger.info(f"使用已完成任務快取數據: {batch_name}")
                return self.cache.get_cached_tasks_by_type(batch_name, "completed")

            # 快取失效，從 API 獲取已完成任務
            logger.info(f"從 API 獲取已完成任務: {batch_name}")
            completed_tasks = self._get_completed_tasks_by_due_date(since=since, until=until, label=batch_name)

            # 儲存到快取
            self.cache.save_tasks_to_cache_by_type(batch_name, completed_tasks, "completed")

            # 回傳快取中的已完成任務
            return self.cache.get_cached_tasks_by_type(batch_name, "completed")

        except Exception as e:
            logger.error(f"獲取已完成任務失敗: {e}")
            # 如果 API 失敗，嘗試返回快取數據（即使可能過期）
            try:
                cached_tasks = self.cache.get_cached_tasks_by_type(batch_name, "completed")
                if cached_tasks:
                    logger.warning(f"API 失敗，使用過期已完成任務快取: {batch_name}")
                    return cached_tasks
            except Exception:
                pass
            raise

    def add_task(
        self, batch_name: str, content: str, description: str = "", due_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """新增任務 - 遠端優先"""
        try:
            # 1. 先呼叫 Todoist API
            remote_task = self.todoist.add_task(
                content=content, description=description, labels=[batch_name], due_string=due_date if due_date else None
            )

            # 2. 成功後更新快取
            self.cache.save_task_to_cache(batch_name, remote_task, "active")

            # 3. 返回快取任務
            cached_task = self.cache.get_task_from_cache(remote_task.id)
            if cached_task:
                return {"success": True, "task": cached_task}
            return {"success": False, "error": "無法找到新增的任務"}

        except Exception as e:
            logger.error(f"新增任務失敗: {e}")
            return {"success": False, "error": str(e)}

    def delete_task(self, task_id: str) -> bool:
        """刪除任務 - 遠端優先"""
        try:
            # 1. 先呼叫 API
            if self.todoist.delete_task(task_id):
                # 2. 成功後更新快取
                self.cache.delete_task_from_cache(task_id)
                return True
            return False
        except Exception as e:
            logger.error(f"刪除任務失敗: {e}")
            return False

    def complete_task(self, task_id: str) -> bool:
        """完成任務 - 遠端優先"""
        try:
            # 1. 先呼叫 API (使用正確的方法名)
            # Todoist API v2 使用 complete_task 方法
            self.todoist.complete_task(task_id)

            # 2. 成功後更新快取
            self.cache.mark_task_completed_in_cache(task_id)

            return True
        except Exception as e:
            logger.error(f"完成任務失敗: {e}")
            return False

    def uncomplete_task(self, task_id: str) -> bool:
        """取消完成任務 - 遠端優先"""
        try:
            # 1. 先呼叫 API
            self.todoist.uncomplete_task(task_id)

            # 2. 成功後更新快取
            self.cache.mark_task_uncompleted_in_cache(task_id)

            return True
        except Exception as e:
            logger.error(f"取消完成任務失敗: {e}")
            return False

    def update_task(
        self, task_id: str, content: Optional[str] = None, description: Optional[str] = None
    ) -> bool:
        """更新任務 - 遠端優先"""
        try:
            # 1. 先呼叫 API
            update_data = {}
            if content is not None:
                update_data["content"] = content
            if description is not None:
                update_data["description"] = description

            self.todoist.update_task(task_id=task_id, **update_data)

            # 2. 成功後更新快取
            self.cache.update_task_in_cache(task_id, content, description)

            return True
        except Exception as e:
            logger.error(f"更新任務失敗: {e}")
            return False


def main():
    batch_name = "山上黑-陳世平25'0304"

    # 測試直接 API 調用
    task_iter = todoist.get_tasks(label=batch_name)
    api_tasks: list[Task] = [task for task_list in task_iter for task in task_list]
    print(f"Direct API tasks found: {len(api_tasks)}")

    todoservice = TodoService(todoist, TodoistCacheService())

    # 測試分離的活動任務獲取（快速）
    print("\n=== Testing Active Tasks (Fast) ===")
    active_tasks = todoservice.get_active_tasks_with_cache(batch_name)
    print(f"Active tasks found: {len(active_tasks)}")
    if active_tasks:
        print(f"Sample active task: {active_tasks[0]['content']}")

    # 測試分離的已完成任務獲取（慢）
    print("\n=== Testing Completed Tasks (Slow) ===")
    since = datetime.now() - timedelta(days=30)
    until = datetime.now()
    completed_tasks = todoservice.get_completed_tasks_with_cache(batch_name, since, until)
    print(f"Completed tasks found: {len(completed_tasks)}")

    # 測試快取性能
    print("\n=== Testing Cache Performance ===")
    start_time = datetime.now()
    active_tasks_cached = todoservice.get_active_tasks_with_cache(batch_name)
    cache_time = (datetime.now() - start_time).total_seconds() * 1000
    print(f"Active tasks cached retrieval: {len(active_tasks_cached)} tasks in {cache_time:.2f}ms")


if __name__ == "__main__":
    main()
