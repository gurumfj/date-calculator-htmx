import json
import logging
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from todoist_api_python.api import TodoistAPI
from todoist_api_python.models import Task

from server.config import get_settings

logger = logging.getLogger(__name__)

todoist_token = get_settings().TODOIST_API_TOKEN
if not todoist_token:
    raise ValueError("TODOIST_API_TOKEN is not set")
todoist = TodoistAPI(todoist_token)


class TodoistCacheService:
    """Todoist 快取服務，專注於本地 SQLite 快取操作"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, db_path: str = "./data/sqlite.db"):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, db_path: str = "./data/sqlite.db"):
        if not hasattr(self, "_initialized"):
            self.db_path = db_path
            self._db_lock = threading.Lock()  # 線程鎖防止並發問題
            self._init_cache_table()
            self._initialized = True

    @contextmanager
    def _get_connection(self):
        """安全的資料庫連線管理"""
        with self._db_lock:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            try:
                # 設定 WAL 模式提高並發性能
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA synchronous=NORMAL")
                conn.execute("PRAGMA temp_store=MEMORY")
                conn.execute("PRAGMA mmap_size=268435456")  # 256MB
                yield conn
            finally:
                conn.close()

    def _init_cache_table(self):
        """初始化快取表"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS todoist_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    batch_name TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    task_type TEXT NOT NULL,
                    content TEXT,
                    description TEXT,
                    due_date TEXT,
                    completed_at TEXT,
                    labels TEXT,
                    priority INTEGER,
                    created_at TEXT,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    cached_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(batch_name, task_id, task_type)
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_todoist_cache_batch_name 
                ON todoist_cache(batch_name)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_todoist_cache_cached_at 
                ON todoist_cache(cached_at)
            """)

            conn.commit()

    def is_cache_valid(self, batch_name: str, max_age_minutes: int = 60) -> bool:
        """檢查快取是否有效"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cutoff_time = datetime.now() - timedelta(minutes=max_age_minutes)
            cursor.execute(
                """
                SELECT COUNT(*) FROM todoist_cache 
                WHERE batch_name = ? AND cached_at > ?
            """,
                (batch_name, cutoff_time.isoformat()),
            )

            count = cursor.fetchone()[0]
            return count > 0

    def get_cached_tasks(self, batch_name: str) -> List[Dict[str, Any]]:
        """從快取取得任務"""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT * FROM todoist_cache 
                WHERE batch_name = ? 
                ORDER BY task_type, created_at DESC
            """,
                (batch_name,),
            )

            tasks = []
            for row in cursor.fetchall():
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

    def save_tasks_to_cache(self, batch_name: str, active_tasks: List[Task], completed_tasks: List[Task]):
        """儲存任務到快取"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 清除舊快取
            cursor.execute("DELETE FROM todoist_cache WHERE batch_name = ?", (batch_name,))

            # 儲存活動任務
            for task in active_tasks:
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO todoist_cache 
                    (batch_name, task_id, task_type, content, description, due_date, 
                     labels, priority, created_at, cached_at)
                    VALUES (?, ?, 'active', ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        batch_name,
                        task.id,
                        task.content,
                        task.description,
                        task.due.date if task.due else None,
                        json.dumps(task.labels),
                        task.priority,
                        task.created_at,
                        datetime.now().isoformat(),
                    ),
                )

            # 儲存已完成任務
            for task in completed_tasks:
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO todoist_cache 
                    (batch_name, task_id, task_type, content, description, due_date,
                     completed_at, labels, priority, created_at, cached_at)
                    VALUES (?, ?, 'completed', ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        batch_name,
                        task.id,
                        task.content,
                        task.description,
                        task.due.date if task.due else None,
                        task.completed_at,
                        json.dumps(task.labels),
                        task.priority,
                        task.created_at,
                        datetime.now().isoformat(),
                    ),
                )

            conn.commit()

    def clear_expired_cache(self, max_age_hours: int = 24) -> int:
        """清理過期快取"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            cursor.execute(
                """
                DELETE FROM todoist_cache WHERE cached_at < ?
            """,
                (cutoff_time.isoformat(),),
            )

            deleted_count = cursor.rowcount
            conn.commit()
            return deleted_count

    def save_task_to_cache(self, batch_name: str, task: Task, task_type: str = "active"):
        """儲存單個任務到快取"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT OR REPLACE INTO todoist_cache 
                (batch_name, task_id, task_type, content, description, due_date, 
                 labels, priority, created_at, cached_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    batch_name,
                    task.id,
                    task_type,
                    task.content,
                    task.description,
                    task.due.date if task.due else None,
                    json.dumps(task.labels),
                    task.priority,
                    task.created_at,
                    datetime.now().isoformat(),
                ),
            )

            conn.commit()

    def delete_task_from_cache(self, batch_name: str, task_id: str):
        """從快取刪除任務"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                DELETE FROM todoist_cache 
                WHERE batch_name = ? AND task_id = ?
            """,
                (batch_name, task_id),
            )

            conn.commit()

    def mark_task_completed_in_cache(self, batch_name: str, task_id: str):
        """在快取中標記任務為完成"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE todoist_cache 
                SET task_type = 'completed', 
                    completed_at = ?,
                    updated_at = ?
                WHERE batch_name = ? AND task_id = ?
            """,
                (datetime.now().isoformat(), datetime.now().isoformat(), batch_name, task_id),
            )

            conn.commit()

    def update_task_in_cache(
        self, batch_name: str, task_id: str, content: Optional[str] = None, description: Optional[str] = None
    ):
        """更新快取中的任務"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            update_fields = []
            params = []

            if content is not None:
                update_fields.append("content = ?")
                params.append(content)

            if description is not None:
                update_fields.append("description = ?")
                params.append(description)

            if update_fields:
                update_fields.append("updated_at = ?")
                params.extend([datetime.now().isoformat(), batch_name, task_id])

                cursor.execute(
                    f"""
                    UPDATE todoist_cache 
                    SET {", ".join(update_fields)}
                    WHERE batch_name = ? AND task_id = ?
                """,
                    params,
                )

            conn.commit()

    def get_task_from_cache(self, batch_name: str, task_id: str) -> Optional[Dict[str, Any]]:
        """從快取獲取單個任務"""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT * FROM todoist_cache 
                WHERE batch_name = ? AND task_id = ?
            """,
                (batch_name, task_id),
            )

            row = cursor.fetchone()

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
        tasks: list[Task] = [task for task_list in tasks_iter for task in task_list]
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

    def get_tasks_with_cache(
        self, batch_name: str, since: datetime, until: datetime, force_refresh: bool = False
    ) -> List[Dict[str, Any]]:
        """帶快取的任務查詢"""
        try:
            # 檢查快取是否有效
            if not force_refresh and self.cache.is_cache_valid(batch_name, max_age_minutes=60):
                logger.info(f"使用快取數據: {batch_name}")
                return self.cache.get_cached_tasks(batch_name)

            # 快取失效，從 API 獲取
            logger.info(f"從 API 獲取數據: {batch_name}")
            active_tasks = self._get_tasks_by_label(batch_name)

            completed_tasks = self._get_completed_tasks_by_due_date(since=since, until=until, label=batch_name)

            # 儲存到快取
            self.cache.save_tasks_to_cache(batch_name, active_tasks, completed_tasks)

            # 回傳快取中的任務
            return self.cache.get_cached_tasks(batch_name)

        except Exception as e:
            logger.error(f"獲取任務失敗: {e}")
            # 如果 API 失敗，嘗試返回快取數據（即使可能過期）
            try:
                cached_tasks = self.cache.get_cached_tasks(batch_name)
                if cached_tasks:
                    logger.warning(f"API 失敗，使用過期快取: {batch_name}")
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

            return {"success": True, "task_id": remote_task.id, "content": remote_task.content}

        except Exception as e:
            logger.error(f"新增任務失敗: {e}")
            return {"success": False, "error": str(e)}

    def delete_task(self, batch_name: str, task_id: str) -> bool:
        """刪除任務 - 遠端優先"""
        try:
            # 1. 先呼叫 API
            self.todoist.delete_task(task_id)

            # 2. 成功後更新快取
            self.cache.delete_task_from_cache(batch_name, task_id)

            return True
        except Exception as e:
            logger.error(f"刪除任務失敗: {e}")
            return False

    def complete_task(self, batch_name: str, task_id: str) -> bool:
        """完成任務 - 遠端優先"""
        try:
            # 1. 先呼叫 API (使用正確的方法名)
            # Todoist API v2 使用 complete_task 方法
            self.todoist.complete_task(task_id)

            # 2. 成功後更新快取
            self.cache.mark_task_completed_in_cache(batch_name, task_id)

            return True
        except Exception as e:
            logger.error(f"完成任務失敗: {e}")
            return False

    def update_task(
        self, batch_name: str, task_id: str, content: Optional[str] = None, description: Optional[str] = None
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
            self.cache.update_task_in_cache(batch_name, task_id, content, description)

            return True
        except Exception as e:
            logger.error(f"更新任務失敗: {e}")
            return False


def main():
    # TODO: 創建依賴注入
    # cache_service = TodoistCacheService()
    # todo_service = TodoService(todoist, cache_service)
    # tasks = todo_service.get_completed_tasks_by_due_date(
    #     since=datetime.now() - timedelta(weeks=1), until=datetime.now(), label="測試2025’0303"
    # )
    # print(f"獲取到 {len(tasks)} 個任務")
    ...


if __name__ == "__main__":
    main()
