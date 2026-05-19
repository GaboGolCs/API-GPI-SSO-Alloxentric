"""Service layer — business logic for worker stats and notifications."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone

from app.exceptions import ForbiddenError
from app.repositories.workers_repository import WorkersRepository
from app.schemas.workers import (
    AreaStats,
    MarkNotificationReadResponse,
    NotificationListResponse,
    NotificationResponse,
    NotificationStatus,
    NotificationType,
    WorkerStatsResponse,
)

_DEFAULT_PERIOD_DAYS = 30


class WorkersService:
    def __init__(self, repo: WorkersRepository) -> None:
        self._repo = repo

    # ─── Stats ────────────────────────────────────────────────────────────

    async def get_my_stats(
        self,
        client_id: str,
        worker_id: str,
        period_days: int = _DEFAULT_PERIOD_DAYS,
    ) -> WorkerStatsResponse:
        since = datetime.now(tz=timezone.utc) - timedelta(days=period_days)

        # Fetch user doc to get assigned areas + last_activity
        # El worker es un usuario con role="worker" en clients/{client_id}/users
        worker_doc = await self._repo.get_user_document(client_id, worker_id)
        assigned_area_ids: list[str] = worker_doc.get("assigned_areas", [])

        # Fetch all reports submitted by this worker in the period
        reports = await self._repo.get_reports_for_worker(client_id, worker_id, since)

        # Aggregate by status
        by_status: dict[str, int] = defaultdict(int)
        by_shift: dict[str, int] = defaultdict(int)
        resolution_hours: list[float] = []
        area_report_map: dict[str, list[dict]] = defaultdict(list)

        for r in reports:
            by_status[r.get("status", "unknown")] += 1
            shift = r.get("shift")
            if shift:
                by_shift[shift] += 1

            area_id = r.get("area_id")
            if area_id:
                area_report_map[area_id].append(r)

            # Resolution time (closed_at - created_at)
            closed_at = r.get("closed_at")
            created_at = r.get("created_at")
            if closed_at and created_at:
                delta = (closed_at - created_at).total_seconds() / 3600
                resolution_hours.append(delta)

        avg_resolution = (
            round(sum(resolution_hours) / len(resolution_hours), 2)
            if resolution_hours
            else None
        )

        # Build per-area stats
        area_stats: list[AreaStats] = []
        for area_id in assigned_area_ids:
            area_reports = area_report_map.get(area_id, [])
            resolved = sum(1 for r in area_reports if r.get("status") == "resolved")
            area_res_hours = []
            for r in area_reports:
                ca = r.get("closed_at")
                cr = r.get("created_at")
                if ca and cr:
                    area_res_hours.append((ca - cr).total_seconds() / 3600)

            area_stats.append(
                AreaStats(
                    area_id=area_id,
                    area_name=r.get("area_name", area_id) if area_reports else area_id,
                    total_reports=len(area_reports),
                    resolved_reports=resolved,
                    pending_reports=len(area_reports) - resolved,
                    avg_resolution_hours=(
                        round(sum(area_res_hours) / len(area_res_hours), 2)
                        if area_res_hours
                        else None
                    ),
                )
            )

        last_activity_raw = worker_doc.get("last_activity_at")
        last_activity: datetime | None = None
        if last_activity_raw:
            last_activity = (
                last_activity_raw
                if isinstance(last_activity_raw, datetime)
                else last_activity_raw.ToDatetime(tzinfo=timezone.utc)
            )

        return WorkerStatsResponse(
            worker_id=worker_id,
            period_days=period_days,
            total_reports_submitted=len(reports),
            reports_by_status=dict(by_status),
            reports_by_shift=dict(by_shift),
            assigned_areas=area_stats,
            avg_resolution_hours=avg_resolution,
            last_activity_at=last_activity,
        )

    # ─── Notifications ────────────────────────────────────────────────────

    async def list_my_notifications(
        self,
        client_id: str,
        worker_id: str,
        *,
        limit: int = 50,
        status_filter: str | None = None,
    ) -> NotificationListResponse:
        raw_notifications = await self._repo.list_notifications(
            client_id, worker_id, limit=limit, status_filter=status_filter
        )
        unread_count = await self._repo.count_unread_notifications(client_id, worker_id)

        notifications = [self._to_notification_response(n) for n in raw_notifications]

        return NotificationListResponse(
            notifications=notifications,
            total=len(notifications),
            unread_count=unread_count,
        )

    async def mark_notification_as_read(
        self,
        client_id: str,
        worker_id: str,
        notification_id: str,
        requesting_user_id: str,
    ) -> MarkNotificationReadResponse:
        # Workers can only mark their own notifications
        if requesting_user_id != worker_id:
            raise ForbiddenError("You can only mark your own notifications as read.")

        updated = await self._repo.mark_notification_read(client_id, worker_id, notification_id)

        return MarkNotificationReadResponse(
            notification_id=notification_id,
            status=NotificationStatus.read,
            read_at=updated["read_at"],
        )

    # ─── Private helpers ──────────────────────────────────────────────────

    @staticmethod
    def _to_notification_response(data: dict) -> NotificationResponse:
        created_at = data.get("created_at")
        if created_at and not isinstance(created_at, datetime):
            created_at = created_at.ToDatetime(tzinfo=timezone.utc)

        read_at = data.get("read_at")
        if read_at and not isinstance(read_at, datetime):
            read_at = read_at.ToDatetime(tzinfo=timezone.utc)

        return NotificationResponse(
            notification_id=data["notification_id"],
            type=NotificationType(data.get("type", "alert")),
            title=data.get("title", ""),
            body=data.get("body", ""),
            status=NotificationStatus(data.get("status", "unread")),
            related_report_id=data.get("related_report_id"),
            related_alert_id=data.get("related_alert_id"),
            created_at=created_at,
            read_at=read_at,
        )
