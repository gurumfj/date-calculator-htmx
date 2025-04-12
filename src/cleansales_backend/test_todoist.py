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


def test_create_and_cleanup_task():
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


def main() -> None:
    labels = api.get_labels()
    print(f"Labels: {labels}")

    label = "批次名稱2025-04-13"
    # ✅ 建立測試任務
    task = api.add_task(
        content="✅ 測試任務 - test_todoist.py",
        due_string="tomorrow at 9am",
        priority=3,
        labels=[label],
    )
    print(f"✅ 建立成功，任務 ID: {task.id}")

    comment = api.add_comment(content="This is a test comment", task_id=task.id)
    print(f"✅ 添加評論成功，評論 ID: {comment.id}")

    # 清理任務
    success = api.delete_task(task.id)
    print(f"🧹 測試任務已刪除，環境清理完畢。{success}")


if __name__ == "__main__":
    main()
