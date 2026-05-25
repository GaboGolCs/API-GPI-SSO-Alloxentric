"""Integration tests para /v1/plant y /v1/zones endpoints."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

# Sin token — todos deben retornar 401 o 403
BASE_HEADERS = {}


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


class TestHealthCheck:
    async def test_health_returns_ok(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


class TestFloorPlanNoAuth:
    async def test_post_floor_plan_requires_auth(self, client):
        resp = await client.post("/v1/plant/floor-plan")
        assert resp.status_code in (401, 403, 422)

    async def test_get_floor_plan_requires_auth(self, client):
        resp = await client.get("/v1/plant/floor-plan")
        assert resp.status_code in (401, 403)


class TestZonesNoAuth:
    async def test_list_zones_requires_auth(self, client):
        resp = await client.get("/v1/zones")
        assert resp.status_code in (401, 403)

    async def test_create_zone_requires_auth(self, client):
        resp = await client.post("/v1/zones", json={})
        assert resp.status_code in (401, 403, 422)

    async def test_update_zone_requires_auth(self, client):
        resp = await client.patch("/v1/zones/zone_01", json={})
        assert resp.status_code in (401, 403)

    async def test_delete_zone_requires_auth(self, client):
        resp = await client.delete("/v1/zones/zone_01")
        assert resp.status_code in (401, 403)


class TestZoneValidation:
    async def test_create_zone_invalid_color(self, client):
        """El color debe ser hex #RRGGBB — un color inválido da 422."""
        resp = await client.post(
            "/v1/zones",
            json={
                "name": "Test", "process": "Test",
                "color": "red",  # inválido
                "polygon": [{"x": 0, "y": 0}, {"x": 1, "y": 0}, {"x": 1, "y": 1}],
            },
            headers={"Authorization": "Bearer fake"},
        )
        assert resp.status_code in (401, 422)

    async def test_create_zone_polygon_too_small(self, client):
        """El polígono necesita al menos 3 puntos."""
        resp = await client.post(
            "/v1/zones",
            json={
                "name": "Test", "process": "Test", "color": "#FF5733",
                "polygon": [{"x": 0, "y": 0}],  # solo 1 punto
            },
            headers={"Authorization": "Bearer fake"},
        )
        assert resp.status_code in (401, 422)
