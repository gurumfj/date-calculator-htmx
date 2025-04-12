"""
測試 FastAPI root 節點
"""

from fastapi.testclient import TestClient

from cleansales_backend.api.app import app

client = TestClient(app)


def test_root_endpoint() -> None:
    """測試健康檢查端點是否正常工作"""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert "status" in response.json()
    assert response.json()["status"] == "healthy"
    assert "api_version" in response.json()
    assert "cache_state" in response.json()


def test_cache_clear_endpoint() -> None:
    """測試緩存清除端點"""
    response = client.get("/cache_clear")
    assert response.status_code == 200
    assert "status" in response.json()
    assert response.json()["status"] == "success"
