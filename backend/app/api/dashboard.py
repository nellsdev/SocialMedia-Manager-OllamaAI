"""Dashboard routes — KPIs and time-series metrics (R020–R022).

Provides GET /dashboard/kpis and GET /dashboard/timeseries backed by
metrics_snapshots. Handles missing data gracefully by returning zeros.
In DEBUG mode, returns deterministic mock data when Supabase is unavailable.
"""

import logging
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from supabase import Client

from app.core.auth_utils import extract_bearer_token
from app.core.config import settings
from app.core.database import get_supabase_client
from app.schemas.dashboard import KpiResponse, TimeSeriesPoint, TimeSeriesResponse

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

logger = logging.getLogger(__name__)

ALLOWED_METRICS = {"followers", "likes", "comments", "reach", "engagement_rate", "saves", "shares"}


def _get_supabase() -> Client:
    return get_supabase_client()


def _require_user(request: Request, supabase: Client) -> dict:
    result = supabase.auth.get_user(extract_bearer_token(request))
    user = result.user
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return {"id": user.id, "email": user.email}


def _require_profile(supabase: Client, user: dict) -> str:
    from app.core.auth_utils import require_profile
    return require_profile(supabase, user["id"])


def _get_account_ids(supabase: Client, profile_id: str) -> list[str]:
    try:
        resp = supabase.table("social_accounts").select("id").eq("profile_id", profile_id).execute()
        return [row["id"] for row in (resp.data or [])]
    except Exception:
        logger.exception("Failed to fetch social_accounts for profile %s", profile_id)
        return []


def _compute_delta(current: float, previous: float) -> float:
    if previous == 0:
        return 0.0
    return round(((current - previous) / previous) * 100, 1)


def _mock_kpis() -> KpiResponse:
    """Deterministic mock KPIs for local dev without Supabase."""
    return KpiResponse(
        followers=3420,
        likes=842,
        comments=127,
        reach=12840,
        engagement_rate=7.5,
        followers_delta=4.2,
        engagement_delta=1.1,
    )


def _mock_timeseries(metric: str, days: int) -> list[TimeSeriesPoint]:
    """Generate deterministic mock time-series points.

    No external deps, uses simple hash-based variation to avoid test flakiness.
    """
    today = date.today()
    base_hash = sum(ord(c) for c in metric)
    points: list[TimeSeriesPoint] = []

    # For followers we generate cumulative growth to mimic realistic trend
    followers_cursor = 3000

    for i in range(days):
        d = (today - timedelta(days=days - 1 - i)).isoformat()[:10]

        if metric == "followers":
            # increment 20-50 per day with deterministic jitter
            inc = 20 + (base_hash + i * 13) % 31  # 20-50
            if i == 0:
                followers_cursor = 3000 + inc
            else:
                followers_cursor += inc
            value = float(followers_cursor)
        elif metric == "likes":
            value = float(400 + (base_hash + i * 53) % 501)  # 400-900
        elif metric == "comments":
            value = float(50 + (base_hash + i * 47) % 101)  # 50-150
        elif metric == "reach":
            value = float(8000 + (base_hash + i * 61) % 7001)  # 8000-15000
        elif metric == "engagement_rate":
            value = round(4.5 + ((base_hash + i * 19) % 41) / 10.0, 1)  # 4.5-8.5
        elif metric in ("saves", "shares"):
            value = float(10 + (base_hash + i * 41) % 71)  # 10-80
        else:
            value = float(100 + (base_hash + i * 31) % 200)

        points.append(TimeSeriesPoint(date=d, value=float(value)))

    return points


@router.get("/kpis", response_model=KpiResponse)
async def get_kpis(request: Request, supabase: Client = Depends(_get_supabase)):
    """Return current KPIs with deltas (R020)."""
    try:
        try:
            user = _require_user(request, supabase)
            profile_id = _require_profile(supabase, user)
            account_ids = _get_account_ids(supabase, profile_id)
        except HTTPException:
            if settings.DEBUG:
                logger.warning("Supabase unavailable — returning mock KPIs (DEBUG)")
                return _mock_kpis()
            raise
        except Exception:
            if settings.DEBUG:
                logger.warning("Supabase unavailable — returning mock KPIs (DEBUG)")
                return _mock_kpis()
            raise

        # No connected accounts -> empty KPIs (or mock in DEBUG)
        if not account_ids:
            if settings.DEBUG:
                logger.warning("No linked accounts — returning mock KPIs (DEBUG)")
                return _mock_kpis()
            return KpiResponse()

        # Fetch latest 2 snapshots ordered by metric_date desc
        try:
            # Supabase-py supports .in_ for IN filter
            query = supabase.table("metrics_snapshots").select("*").order("metric_date", desc=True).limit(2)
            if len(account_ids) == 1:
                query = query.eq("social_account_id", account_ids[0])
            else:
                # Use in_ if available, fallback to first id filter
                try:
                    query = query.in_("social_account_id", account_ids)
                except AttributeError:
                    query = query.eq("social_account_id", account_ids[0])

            resp = query.execute()
            rows = resp.data or []
        except Exception:
            logger.exception("Failed to fetch metrics_snapshots for KPIs")
            rows = []

        if not rows:
            if settings.DEBUG:
                logger.warning("No metrics snapshots — returning mock KPIs (DEBUG)")
                return _mock_kpis()
            return KpiResponse()

        latest = rows[0]
        previous = rows[1] if len(rows) > 1 else None

        followers = int(latest.get("followers") or 0)
        likes = int(latest.get("likes") or 0)
        comments = int(latest.get("comments") or 0)
        reach = int(latest.get("reach") or 0)
        engagement_rate = float(latest.get("engagement_rate") or 0.0)

        # Compute engagement_rate if missing/zero but we have likes/comments/reach
        if engagement_rate == 0.0 and reach > 0:
            engagement_rate = round(((likes + comments) / reach) * 100, 2)

        followers_delta = 0.0
        engagement_delta = 0.0
        if previous:
            prev_followers = int(previous.get("followers") or 0)
            prev_likes = int(previous.get("likes") or 0)
            prev_comments = int(previous.get("comments") or 0)
            prev_reach = int(previous.get("reach") or 0)
            prev_rate = float(previous.get("engagement_rate") or 0.0)
            if prev_rate == 0.0 and prev_reach > 0:
                prev_rate = round(((prev_likes + prev_comments) / prev_reach) * 100, 2)
            followers_delta = _compute_delta(followers, prev_followers)
            engagement_delta = _compute_delta(engagement_rate, prev_rate)

        return KpiResponse(
            followers=followers,
            likes=likes,
            comments=comments,
            reach=reach,
            engagement_rate=engagement_rate,
            followers_delta=followers_delta,
            engagement_delta=engagement_delta,
        )
    except HTTPException:
        if settings.DEBUG:
            logger.warning("Supabase unavailable — returning mock KPIs (DEBUG)")
            return _mock_kpis()
        raise
    except Exception:
        logger.exception("Unexpected error in get_kpis")
        if settings.DEBUG:
            logger.warning("Supabase unavailable — returning mock KPIs (DEBUG)")
            return _mock_kpis()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch KPIs")


@router.get("/timeseries", response_model=TimeSeriesResponse)
async def get_timeseries(
    request: Request,
    metric: str = Query("followers", description="Metric name"),
    days: int = Query(30, ge=1, le=90, description="Number of days"),
    supabase: Client = Depends(_get_supabase),
):
    """Return metric time series over the last N days (R021)."""
    if metric not in ALLOWED_METRICS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid metric. Allowed: {', '.join(sorted(ALLOWED_METRICS))}")

    try:
        try:
            user = _require_user(request, supabase)
            profile_id = _require_profile(supabase, user)
            account_ids = _get_account_ids(supabase, profile_id)
        except HTTPException:
            if settings.DEBUG:
                logger.warning("Supabase unavailable — returning mock timeseries (DEBUG)")
                return TimeSeriesResponse(metric=metric, days=days, data=_mock_timeseries(metric, days))
            raise
        except Exception:
            if settings.DEBUG:
                logger.warning("Supabase unavailable — returning mock timeseries (DEBUG)")
                return TimeSeriesResponse(metric=metric, days=days, data=_mock_timeseries(metric, days))
            raise

        if not account_ids:
            if settings.DEBUG:
                logger.warning("No linked accounts — returning mock timeseries (DEBUG)")
                return TimeSeriesResponse(metric=metric, days=days, data=_mock_timeseries(metric, days))
            return TimeSeriesResponse(metric=metric, days=days, data=[])

        # Date window
        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)

        try:
            # Fetch snapshots within window, ordered ascending
            query = (
                supabase.table("metrics_snapshots")
                .select("metric_date, followers, likes, comments, reach, engagement_rate, saves, shares")
                .gte("metric_date", start_date.isoformat())
                .lte("metric_date", end_date.isoformat())
                .order("metric_date", desc=False)
                .limit(days)
            )
            if len(account_ids) == 1:
                query = query.eq("social_account_id", account_ids[0])
            else:
                try:
                    query = query.in_("social_account_id", account_ids)
                except AttributeError:
                    query = query.eq("social_account_id", account_ids[0])

            resp = query.execute()
            rows = resp.data or []
        except Exception:
            logger.exception("Failed to fetch timeseries for metric %s", metric)
            rows = []

        # If filtered query returned nothing, fallback to latest N rows (ascending)
        if not rows:
            try:
                fallback = supabase.table("metrics_snapshots").select("metric_date, followers, likes, comments, reach, engagement_rate, saves, shares").order("metric_date", desc=True).limit(days)
                if len(account_ids) == 1:
                    fallback = fallback.eq("social_account_id", account_ids[0])
                else:
                    try:
                        fallback = fallback.in_("social_account_id", account_ids)
                    except AttributeError:
                        fallback = fallback.eq("social_account_id", account_ids[0])
                resp2 = fallback.execute()
                rows = list(reversed(resp2.data or []))
            except Exception:
                logger.exception("Fallback timeseries fetch failed")
                rows = []

        if not rows:
            if settings.DEBUG:
                logger.warning("No metrics snapshots — returning mock timeseries (DEBUG)")
                return TimeSeriesResponse(metric=metric, days=days, data=_mock_timeseries(metric, days))
            return TimeSeriesResponse(metric=metric, days=days, data=[])

        points: list[TimeSeriesPoint] = []
        for row in rows:
            raw_date = row.get("metric_date")
            if not raw_date:
                continue
            # Normalize date string
            try:
                date_str = str(raw_date)[:10]
            except Exception:
                date_str = str(raw_date)

            value = row.get(metric)
            if value is None:
                # Compute engagement_rate if missing
                if metric == "engagement_rate":
                    r = int(row.get("reach") or 0)
                    if r > 0:
                        value = round(((int(row.get("likes") or 0) + int(row.get("comments") or 0)) / r) * 100, 2)
                    else:
                        value = 0.0
                else:
                    value = 0
            try:
                num = float(value)
            except (TypeError, ValueError):
                num = 0.0
            points.append(TimeSeriesPoint(date=date_str, value=num))

        # If parsing yielded no points but we had rows, treat as empty -> mock in DEBUG
        if not points and settings.DEBUG:
            logger.warning("No valid timeseries points — returning mock timeseries (DEBUG)")
            return TimeSeriesResponse(metric=metric, days=days, data=_mock_timeseries(metric, days))

        return TimeSeriesResponse(metric=metric, days=days, data=points)
    except HTTPException:
        if settings.DEBUG:
            logger.warning("Supabase unavailable — returning mock timeseries (DEBUG)")
            return TimeSeriesResponse(metric=metric, days=days, data=_mock_timeseries(metric, days))
        raise
    except Exception:
        logger.exception("Unexpected error in get_timeseries")
        if settings.DEBUG:
            logger.warning("Supabase unavailable — returning mock timeseries (DEBUG)")
            return TimeSeriesResponse(metric=metric, days=days, data=_mock_timeseries(metric, days))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch time series")
