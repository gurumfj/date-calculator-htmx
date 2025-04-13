from todoist_api_python.api import TodoistAPI

from cleansales_backend.core import get_settings

# ✅ 讀取 .env 檔
settings = get_settings()
API_TOKEN = settings.TODOIST_API_TOKEN

if not API_TOKEN:
    raise ValueError("請在 .env 檔中設定 TODOIST_API_TOKEN")

# ✅ 初始化 API
api = TodoistAPI(API_TOKEN)


# def test_todoist_connectivity():
#     print("🔌 測試連線中...")
#     try:
#         user = api.
#         print(f"✅ 連線成功！你好，{user.full_name}")
#     except Exception as e:
#         print("❌ 連線失敗：", e)
#         return False
#     return True


def test_create_and_cleanup_task() -> None:
    print("📝 建立測試任務...")
    try:
        task = api.add_task(
            content="✅ 測試任務 - test_todoist.py",
            due_string="tomorrow at 9am",
            priority=3,
        )
        print(f"✅ 建立成功，任務 ID: {task.id}")

        # 查詢任務
        task_fetched = api.get_task(task.id)
        print(f"📋 查詢任務內容: {task_fetched.content}")

        # 清理任務
        success = api.delete_task(task.id)
        print(f"🧹 測試任務已刪除，環境清理完畢。{success}")
    except Exception as e:
        print("❌ 發生錯誤：", e)


"""
# 📋 查詢任務內容: Task(assignee_id=None, assigner_id=None, comment_count=1, is_completed=False, content='測試任務Name @test_label', created_at='2025-04-12T18:53:08.355622Z', creator_id='15948005', description='test description.', due=Due(date='2025-04-14', is_recurring=False, string='4月14日', datetime=None, timezone=None), id='9064898674', labels=['test_label', 'test_label2'], order=1, parent_id=None, priority=3, project_id='2175825282', section_id=None, url='https://app.todoist.com/app/task/9064898674', duration=None, sync_id=None)"""


def get_project_id(api: TodoistAPI, project_name: str) -> str:
    projects = api.get_projects()
    if project_name not in [project.name for project in projects]:
        project = api.add_project(name=project_name)
        return project.id
    else:
        return [project.id for project in projects if project.name == project_name][0]


def main() -> None:
    test_create_and_cleanup_task()


if __name__ == "__main__":
    main()
