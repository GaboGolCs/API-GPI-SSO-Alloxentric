from datetime import datetime, timedelta
from app.repositories.dashboard_repo import DashboardRepository
from app.schemas.dashboard import (
    HeatmapResponse, ZoneHeatmap,
    KpisResponse,
    TrendsResponse, TrendDataPoint,
    TopAreasResponse, TopAreaItem,
)


class DashboardService:
    """Lógica de negocio del dashboard. No accede a Firestore directamente."""

    def __init__(self, repository: DashboardRepository):
        self.repository = repository

    # ─── HELPERS ──────────────────────────────────────────────────────────────

    def _calc_risk_score(self, reports: list) -> int:
        """Calcula el score de riesgo (0-100) basado en reportes de una zona."""
        if not reports:
            return 0
        score = 0.0
        now = datetime.utcnow()
        for r in reports:
            base      = 20 if r.get("is_iap") else 10
            created   = r.get("created_at")
            hours_old = 48.0
            if created:
                try:
                    if hasattr(created, "replace"):
                        dt = created.replace(tzinfo=None)
                    else:
                        dt = datetime.fromisoformat(
                            str(created).replace("Z", "").split(".")[0]
                        )
                    hours_old = (now - dt).total_seconds() / 3600
                except Exception:
                    pass
            recency   = 1.5 if hours_old < 24 else (1.2 if hours_old < 72 else 1.0)
            open_mult = 1.3 if r.get("status") != "closed" else 0.5
            score    += base * recency * open_mult
        return min(100, int(score))

    def _risk_level(self, score: int) -> str:
        if score >= 80: return "critical"
        if score >= 60: return "high"
        if score >= 40: return "medium"
        return "low"

    def _trend(self, score: int) -> str:
        if score >= 60: return "rising"
        if score >= 30: return "stable"
        return "falling"

    def _group_by_zone(self, reports: list) -> dict:
        by_zone: dict = {}
        for r in reports:
            zone = r.get("area_id", "Sin zona")
            by_zone.setdefault(zone, []).append(r)
        return by_zone

    def _safe_date_str(self, val) -> str:
        if not val: return ""
        try:
            if hasattr(val, "strftime"): return val.strftime("%Y-%m-%d")
            return str(val)[:10]
        except Exception: return ""

    # ─── HEATMAP ──────────────────────────────────────────────────────────────

    async def get_heatmap(self, client_id: str, period: str = "7d") -> HeatmapResponse:
        reports  = await self.repository.get_all_reports(client_id)
        by_zone  = self._group_by_zone(reports)
        zones    = []

        for name, zone_reports in by_zone.items():
            score      = self._calc_risk_score(zone_reports)
            open_count = sum(1 for r in zone_reports if r.get("status") != "closed")
            iap_count  = sum(1 for r in zone_reports if r.get("is_iap") and r.get("status") != "closed")
            zone_id    = f"zone_{name[:8].lower().replace(' ', '_').replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u')}"

            zones.append(ZoneHeatmap(
                zone_id      = zone_id,
                name         = name,
                risk_score   = score,
                risk_level   = self._risk_level(score),
                open_reports = open_count,
                iap_count    = iap_count,
                trend        = self._trend(score),
                last_updated = datetime.utcnow().isoformat() + "Z",
            ))

        zones.sort(key=lambda z: z.risk_score, reverse=True)

        return HeatmapResponse(
            period     = period,
            updated_at = datetime.utcnow().isoformat() + "Z",
            zones      = zones,
        )

    # ─── KPIs ─────────────────────────────────────────────────────────────────

    async def get_kpis(self, client_id: str, period: str = "30d") -> KpisResponse:
        reports    = await self.repository.get_all_reports(client_id)
        total      = len(reports)
        active_iap = sum(1 for r in reports if r.get("is_iap") and r.get("status") != "closed")
        closed     = sum(1 for r in reports if r.get("status") == "closed")
        now        = datetime.utcnow()

        # Reportes abiertos hace más de 48h = vencidos
        overdue = 0
        for r in reports:
            if r.get("status") == "closed":
                continue
            created = r.get("created_at")
            if created:
                try:
                    dt = created.replace(tzinfo=None) if hasattr(created, "replace") else datetime.fromisoformat(str(created).replace("Z","").split(".")[0])
                    if (now - dt).total_seconds() / 3600 > 48:
                        overdue += 1
                except Exception:
                    pass

        sla_rate     = round((closed / total * 100), 1) if total > 0 else 100.0
        by_zone      = self._group_by_zone(reports)
        scores       = [self._calc_risk_score(reps) for reps in by_zone.values()]
        global_score = int(sum(scores) / len(scores)) if scores else 0

        return KpisResponse(
            period               = period,
            total_reports        = total,
            total_reports_delta  = 12.5,   # TODO: calcular vs período anterior
            active_iap           = active_iap,
            active_iap_delta     = -3.0,
            sla_compliance_rate  = sla_rate,
            overdue_actions      = overdue,
            closed_total         = closed,
            global_risk_score    = global_score,
        )

    # ─── TRENDS ───────────────────────────────────────────────────────────────

    async def get_trends(self, client_id: str, days: int = 7) -> TrendsResponse:
        reports = await self.repository.get_all_reports(client_id)
        now     = datetime.utcnow()
        data    = []

        for i in range(days):
            day      = now - timedelta(days=(days - 1 - i))
            day_str  = day.strftime("%Y-%m-%d")
            day_reps = [r for r in reports if self._safe_date_str(r.get("created_at")) == day_str]

            score      = self._calc_risk_score(day_reps)
            open_count = sum(1 for r in day_reps if r.get("status") != "closed")
            closed     = sum(1 for r in day_reps if r.get("status") == "closed")

            data.append(TrendDataPoint(
                date              = day_str,
                global_risk_score = score,
                open_reports      = open_count,
                new_reports       = len(day_reps),
                closed_reports    = closed,
            ))

        return TrendsResponse(days=days, data=data)

    # ─── TOP AREAS ────────────────────────────────────────────────────────────

    async def get_top_areas(self, client_id: str, limit: int = 5) -> TopAreasResponse:
        reports = await self.repository.get_all_reports(client_id)
        by_zone = self._group_by_zone(reports)

        ranked = []
        for name, zone_reports in by_zone.items():
            score      = self._calc_risk_score(zone_reports)
            open_count = sum(1 for r in zone_reports if r.get("status") != "closed")
            iap_count  = sum(1 for r in zone_reports if r.get("is_iap") and r.get("status") != "closed")
            zone_id    = f"zone_{name[:8].lower().replace(' ', '_')}"
            ranked.append({
                "name": name, "zone_id": zone_id, "score": score,
                "open_count": open_count, "iap_count": iap_count,
            })

        ranked.sort(key=lambda z: z["score"], reverse=True)

        return TopAreasResponse(
            data=[
                TopAreaItem(
                    rank         = i + 1,
                    zone_id      = z["zone_id"],
                    name         = z["name"],
                    risk_score   = z["score"],
                    risk_level   = self._risk_level(z["score"]),
                    trend        = self._trend(z["score"]),
                    open_reports = z["open_count"],
                    iap_count    = z["iap_count"],
                )
                for i, z in enumerate(ranked[:limit])
            ]
        )
