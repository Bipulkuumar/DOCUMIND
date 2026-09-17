import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_health_endpoint_degraded_when_db_down(async_client):
    with patch("app.api.v1.health.check_db_health", new_callable=AsyncMock) as mock_db:
        mock_db.return_value = False
        response = await async_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["database_connected"] is False


@pytest.mark.asyncio
async def test_health_endpoint_healthy_when_db_up(async_client):
    with patch("app.api.v1.health.check_db_health", new_callable=AsyncMock) as mock_db:
        mock_db.return_value = True
        response = await async_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database_connected"] is True


@pytest.mark.asyncio
async def test_metrics_endpoint(async_client):
    response = await async_client.get("/api/v1/metrics")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "documents_processed" in data["data"]
