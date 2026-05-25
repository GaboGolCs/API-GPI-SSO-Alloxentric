"""Unit tests para DigitalTwinService."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.exceptions import ForbiddenError, NotFoundError
from app.repositories.digital_twin_repository import DigitalTwinRepository
from app.schemas.digital_twin import ZoneCreateRequest, ZoneUpdateRequest, PolygonPoint
from app.services.digital_twin_service import DigitalTwinService

CLIENT_ID = "client_abc"
ZONE_ID   = "zone_01HXQ"

POLYGON = [
    PolygonPoint(x=0, y=0),
    PolygonPoint(x=100, y=0),
    PolygonPoint(x=100, y=100),
]

ZONE_DOC = {
    "zone_id":   ZONE_ID,
    "client_id": CLIENT_ID,
    "name":      "Zona A",
    "process":   "Ensamblaje",
    "color":     "#FF5733",
    "polygon":   [{"x": 0, "y": 0}, {"x": 100, "y": 0}, {"x": 100, "y": 100}],
    "created_at": "2026-05-01T00:00:00+00:00",
    "updated_at": "2026-05-01T00:00:00+00:00",
}


@pytest.fixture
def mock_repo() -> DigitalTwinRepository:
    repo = AsyncMock(spec=DigitalTwinRepository)
    repo.list_zones.return_value = [ZONE_DOC]
    repo.create_zone.return_value = ZONE_DOC
    repo.update_zone.return_value = ZONE_DOC
    repo.delete_zone.return_value = None
    repo.get_floor_plan_url.return_value = "https://storage.googleapis.com/bucket/floor.png"
    return repo


@pytest.fixture
def service(mock_repo) -> DigitalTwinService:
    storage_mock = MagicMock()
    return DigitalTwinService(mock_repo, storage_mock)


class TestListZones:
    async def test_returns_zone_list(self, service, mock_repo):
        result = await service.list_zones(CLIENT_ID)
        assert result.total == 1
        assert result.data[0].zone_id == ZONE_ID
        mock_repo.list_zones.assert_awaited_once_with(CLIENT_ID)

    async def test_empty_returns_zero(self, service, mock_repo):
        mock_repo.list_zones.return_value = []
        result = await service.list_zones(CLIENT_ID)
        assert result.total == 0
        assert result.data == []


class TestCreateZone:
    async def test_creates_and_returns_zone(self, service, mock_repo):
        payload = ZoneCreateRequest(
            name="Zona A", process="Ensamblaje", color="#FF5733", polygon=POLYGON
        )
        result = await service.create_zone(CLIENT_ID, payload)
        assert result.zone_id == ZONE_ID
        mock_repo.create_zone.assert_awaited_once()


class TestUpdateZone:
    async def test_partial_update(self, service, mock_repo):
        payload = ZoneUpdateRequest(name="Zona B")
        result  = await service.update_zone(CLIENT_ID, ZONE_ID, payload)
        assert result.zone_id == ZONE_ID
        called_data = mock_repo.update_zone.call_args[0][2]
        assert "name" in called_data
        assert "process" not in called_data


class TestDeleteZone:
    async def test_admin_can_delete(self, service, mock_repo):
        result = await service.delete_zone(CLIENT_ID, ZONE_ID, "admin")
        assert result.deleted is True
        mock_repo.delete_zone.assert_awaited_once_with(CLIENT_ID, ZONE_ID)

    async def test_worker_cannot_delete(self, service):
        with pytest.raises(ForbiddenError):
            await service.delete_zone(CLIENT_ID, ZONE_ID, "worker")


class TestGetFloorPlan:
    async def test_returns_url_when_exists(self, service, mock_repo):
        result = await service.get_floor_plan(CLIENT_ID)
        assert result.has_floor_plan is True
        assert "storage.googleapis.com" in result.floor_plan_url

    async def test_no_floor_plan(self, service, mock_repo):
        mock_repo.get_floor_plan_url.return_value = None
        result = await service.get_floor_plan(CLIENT_ID)
        assert result.has_floor_plan is False
        assert result.floor_plan_url is None
