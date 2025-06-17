#!/usr/bin/env python3
"""
SQL測試運行器
使用方式：
    uv run python tests/sql/test_runner.py
    uv run pytest tests/sql/
"""

import sys
from pathlib import Path

# 將專案根目錄加入Python路徑
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    import pytest
    
    # 運行SQL測試
    test_dir = Path(__file__).parent
    exit_code = pytest.main([
        str(test_dir),
        "-v",  # 詳細輸出
        "--tb=short",  # 簡短的錯誤追蹤
        "--strict-markers",  # 嚴格的標記模式
    ])
    
    sys.exit(exit_code)