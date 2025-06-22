from todoist_service import TodoService, TodoistCacheService, todoist

def main():
    # 創建依賴注入
    cache_service = TodoistCacheService()
    todo_service = TodoService(todoist, cache_service)
    
    # 測試快取功能
    batch_name = "測試2025'0303"
    tasks = todo_service.get_tasks_with_cache(batch_name)
    print(f"獲取到 {len(tasks)} 個任務")

if __name__ == "__main__":
    main()