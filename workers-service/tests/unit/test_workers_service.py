"""Unit tests for WorkersService."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.exceptions import ForbiddenError
from app.repositories.workers_repository import WorkersRepository
from app.schemas.workers import NotificationStatus, WorkerStatsResponse
from app.services.workers_service import WorkersService

CLIENT_ID = "client_abc"
WORKER_ID = "user_worker_01"


def _make_report(status: str = "open", shift: str = "morning", area_id: str = "area_1") -> dict:
    return {
        "report_id": "rep_01",
        "status": status,
        "shift": shift,
        "area_id": area_id,
        "area_name": "Zona A",
        "reported_by": WORKER_ID,
        "created_at": datetime.now(tz=timezone.utc) - timedelta(hours=5),
        "closed_at": datetime.now(tz=timezone.utc) if status == "resolved" else None,
    }


@pytest.fixture
def mock_repo() -> WorkersRepository:
    repo = AsyncMock(spec=WorkersRepository)
    repo.get_user_document.return_value = {
        "user_id": WORKER_ID,
        "assigned_areas": ["area_1"],
        "last_activity_at": None,
    }
    repo.get_reports_for_worker.return_value = [
        _make_report("resolved", "morning", "area_1"),
        _make_report("open", "afternoon", "area_1"),
    ]
    repo.count_unread_notifications.return_value = 2
    return repo


@pytest.fixture
def service(mock_repo: WorkersRepository) -> WorkersService:
    return WorkersService(mock_repo)


class TestGetMyStats:
    async def test_returns_correct_totals(
        self, service: WorkersService, mock_repo: WorkersRepository
    ) -> None:
        result = await service.get_my_stats(CLIENT_ID, WORKER_ID)

        assert isinstance(result, WorkerStatsResponse)
        assert result.total_reports_submitted == 2
        assert result.reports_by_status["resolved"] == 1
        assert result.reports_by_status["open"] == 1

    async def test_by_shift_aggregation(
        self, service: WorkersService, mock_repo: WorkersRepository
    ) -> None:
        result = await service.get_my_stats(CLIENT_ID, WORKER_ID)

        assert result.reports_by_shift["morning"] == 1
        assert result.reports_by_shift["afternoon"] == 1

    async def test_area_stats_built(
        self, service: WorkersService, mock_repo: WorkersRepository
    ) -> None:
        result = await service.get_my_stats(CLIENT_ID, WORKER_ID)

        assert len(result.assigned_areas) == 1
        area = result.assigned_areas[0]
        assert area.area_id == "area_1"
        assert area.total_reports == 2
        assert area.resolved_reports == 1
        assert area.pending_reports == 1

    async def test_no_reports_returns_zeros(
        self, service: WorkersService, mock_repo: WorkersRepository
    ) -> None:
        mock_repo.get_reports_for_worker.return_value = []
        result = await service.get_my_stats(CLIENT_ID, WORKER_ID)

        assert result.total_reports_submitted == 0
        assert result.avg_resolution_hours is None


class TestMarkNotificationAsRead:
    async def test_raises_forbidden_if_different_user(
        self, service: WorkersService
    ) -> None:
        with pytest.raises(ForbiddenError):
            await service.mark_notification_as_read(
                client_id=CLIENT_ID,
                worker_id=WORKER_ID,
                notification_id="notif_01",
                requesting_user_id="other_user",
            )

    async def test_marks_read_for_own_notification(
        self, service: WorkersService, mock_repo: WorkersRepository
    ) -> None:
        now = datetime.now(tz=timezone.utc)
        mock_repo.mark_notification_read.return_value = {
            "notification_id": "notif_01",
            "status": "read",
            "read_at": now,
        }

        result = await service.mark_notification_as_read(
            client_id=CLIENT_ID,
            worker_id=WORKER_ID,
            notification_id="notif_01",
            requesting_user_id=WORKER_ID,
        )

        assert result.status == NotificationStatus.read
        assert result.notification_id == "notif_01"
        mock_repo.mark_notification_read.assert_awaited_once_with(
            CLIENT_ID, WORKER_ID, "notif_01"
        )
