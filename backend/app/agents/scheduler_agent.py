"""Scheduler Agent (3.6).

Manages APScheduler jobs for automated post publishing to Instagram.
Provides schedule, cancel, publish, and retry operations with exponential
back-off for rate-limit and failure scenarios (R017, R018).
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

from app.agents.base import BaseAgent
from app.core.config import settings

logger = logging.getLogger(__name__)

# Maximum number of publish retry attempts
MAX_RETRIES = 3
# Base delay in seconds for exponential back-off
RETRY_BASE_DELAY = 60  # 1 minute
# Maximum delay cap
RETRY_MAX_DELAY = 3600  # 1 hour


@dataclass
class PublishResult:
    success: bool
    status: str  # published / failed / retrying
    platform_post_id: str | None = None
    platform_permalink: str | None = None
    failure_reason: str | None = None


# ---------------------------------------------------------------------------
# Singleton scheduler instance
# ---------------------------------------------------------------------------

_scheduler: AsyncIOScheduler | None = None


def _get_scheduler_db_url() -> str:
    """Build a PostgreSQL URL from the Supabase URL for APScheduler."""
    url = settings.SUPABASE_URL
    if url.startswith("http://"):
        url = url.replace("http://", "postgresql://", 1)
    elif url.startswith("https://"):
        url = url.replace("https://", "postgresql://", 1)
    return url


async def reconcile_scheduled_jobs() -> None:
    """Re-register pending jobs from DB on startup."""
    from app.core.database import get_supabase_service_client

    supabase = get_supabase_service_client()
    resp = (
        supabase.table("scheduler_jobs")
        .select("*")
        .eq("status", "scheduled")
        .execute()
    )

    for job_row in resp.data:
        post_id = job_row["post_id"]
        scheduled_for = datetime.fromisoformat(job_row["scheduled_at"])
        if scheduled_for > datetime.now(timezone.utc):
            try:
                _scheduler.add_job(
                    publish_post,
                    trigger="date",
                    run_date=scheduled_for,
                    args=[post_id],
                    id=f"post_{post_id}",
                    replace_existing=True,
                )
                logger.info("Re-registered job for post %s", post_id)
            except Exception as e:
                logger.error("Failed to re-register job for post %s: %s", post_id, e)


async def publish_post(post_id: str) -> None:
    """Top-level coroutine for APScheduler jobs to call."""
    from app.agents.scheduler_agent import SchedulerAgent

    agent = SchedulerAgent()
    result = await agent.publish_post(post_id)
    logger.info("Reconciled publish for post %s: %s", post_id, result.status)


def get_scheduler() -> AsyncIOScheduler:
    """Return the shared APScheduler instance, creating it if needed."""
    global _scheduler
    if _scheduler is None:
        _jobstore = SQLAlchemyJobStore(url=_get_scheduler_db_url())
        _scheduler = AsyncIOScheduler(jobstores={"default": _jobstore})
        _scheduler.start()
        logger.info("APScheduler started (SQL job store)")
        _scheduler.add_job(
            reconcile_scheduled_jobs,
            trigger="date",
            run_date=datetime.now(timezone.utc),
            id="reconcile_startup",
        )
    return _scheduler


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------


class SchedulerAgent(BaseAgent):
    """Manages APScheduler jobs for post publishing.

    Uses the shared AsyncIOScheduler singleton. Each scheduled post is
    registered as a date-triggered job that calls :meth:`publish_post`.
    """

    async def schedule_post(self, post_id: str, scheduled_for: datetime) -> str:
        """Schedule a post for publishing at *scheduled_for*.

        Returns the APScheduler job ID.
        """
        scheduler = get_scheduler()
        job = scheduler.add_job(
            self._publish_wrapper,
            trigger="date",
            run_date=scheduled_for,
            args=[post_id],
            id=f"post_{post_id}",
            replace_existing=True,
        )
        logger.info("Scheduled post %s for %s (job %s)", post_id, scheduled_for, job.id)
        return job.id

    async def cancel_post(self, post_id: str) -> bool:
        """Cancel a scheduled post."""
        scheduler = get_scheduler()
        job_id = f"post_{post_id}"
        try:
            scheduler.remove_job(job_id)
            logger.info("Cancelled scheduled post %s", post_id)
            return True
        except Exception as exc:
            logger.warning("Failed to cancel post %s: %s", post_id, exc)
            return False

    async def publish_post(self, post_id: str) -> PublishResult:
        """Publish a post *now* via the Instagram Graph API.

        This is called both for immediate publishing and when the scheduler
        triggers. The actual Graph API calls are attempted with retry logic.
        """
        supabase = None
        try:
            from app.core.database import get_supabase_service_client

            supabase = get_supabase_service_client()
        except Exception as exc:
            logger.error("Failed to get DB client: %s", exc)
            return PublishResult(success=False, status="failed", failure_reason=str(exc))

        # Fetch the post
        post_resp = supabase.table("content_posts").select("*").eq("id", post_id).maybe_single().execute()
        if not post_resp.data:
            return PublishResult(success=False, status="failed", failure_reason="Post not found")

        post = post_resp.data

        # Fetch the IG account
        ig_account_id = post.get("ig_account_id")
        if not ig_account_id:
            supabase.table("content_posts").update({
                "status": "failed",
                "failure_reason": "No Instagram account linked",
            }).eq("id", post_id).execute()
            return PublishResult(success=False, status="failed", failure_reason="No Instagram account linked")

        account_resp = supabase.table("social_accounts").select("*").eq("id", ig_account_id).maybe_single().execute()
        if not account_resp.data:
            return PublishResult(success=False, status="failed", failure_reason="Instagram account not found")

        account = account_resp.data
        access_token = account.get("access_token", "")

        # Attempt publish with retry
        result = await self._publish_with_retry(
            post_id=post_id,
            ig_user_id=account["account_id"],
            access_token=access_token,
            media_type=post.get("format", "CAROUSEL"),
            media_url=post.get("media_urls", [None])[0] if post.get("media_urls") else None,
            caption=post.get("caption", ""),
        )

        # Update the post status based on result — each DB call wrapped individually
        # so a DB failure after a successful Instagram publish doesn't cause
        # duplicate retries (the post IS published, we just can't track it).
        if result.status == "published":
            try:
                supabase.table("content_posts").update({
                    "status": "published",
                    "published_at": datetime.now(timezone.utc).isoformat(),
                    "failure_reason": None,
                    "platform_post_id": result.platform_post_id,
                    "platform_permalink": result.platform_permalink,
                }).eq("id", post_id).execute()
            except Exception as e:
                logger.error("CRITICAL: Post %s published on Instagram but DB update failed: %s", post_id, e)
                # Don't raise — the post IS published, we just can't track it
        else:
            try:
                update_data = {"status": result.status}
                if result.failure_reason:
                    update_data["failure_reason"] = result.failure_reason
                supabase.table("content_posts").update(update_data).eq("id", post_id).execute()
            except Exception as e:
                logger.warning("Failed to update post status for post %s: %s", post_id, e)

        # Update scheduler job status
        try:
            supabase.table("scheduler_jobs").update({
                "status": "completed" if result.status == "published" else "failed",
                "executed_at": datetime.now(timezone.utc).isoformat(),
            }).eq("post_id", post_id).eq("status", "scheduled").execute()
        except Exception as e:
            logger.warning("Failed to update scheduler job status for post %s: %s", post_id, e)

        return result

    async def retry_failed(self, post_id: str) -> PublishResult:
        """Retry publishing a failed post."""
        return await self.publish_post(post_id)

    async def _publish_wrapper(self, post_id: str) -> None:
        """Wrapper for APScheduler jobs (runs publish_post)."""
        result = await self.publish_post(post_id)
        logger.info(
            "Publish result for post %s: success=%s status=%s",
            post_id,
            result.success,
            result.status,
        )

    async def _publish_with_retry(
        self,
        post_id: str,
        ig_user_id: str,
        access_token: str,
        media_type: str,
        media_url: str | None,
        caption: str,
    ) -> PublishResult:
        """Attempt publishing with exponential back-off retry logic (4.3/R018)."""
        import httpx

        last_error = ""

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    # Step 1: Create media container
                    media_payload = {
                        "media_type": media_type.upper(),
                        "caption": caption,
                        "access_token": access_token,
                    }
                    if media_url:
                        if media_type.upper() in ("IMAGE", "CAROUSEL"):
                            media_payload["image_url"] = media_url
                        else:
                            media_payload["video_url"] = media_url

                    create_resp = await client.post(
                        f"https://graph.facebook.com/v18.0/{ig_user_id}/media",
                        json=media_payload,
                    )
                    create_data = create_resp.json()

                    # Check for rate-limit
                    if create_resp.status_code == 429:
                        delay = min(RETRY_BASE_DELAY * (2 ** (attempt - 1)), RETRY_MAX_DELAY)
                        logger.warning(
                            "Rate limited on attempt %d/%d for post %s. Retrying in %ds",
                            attempt, MAX_RETRIES, post_id, delay,
                        )
                        await asyncio.sleep(delay)
                        # Update retry count in scheduler_jobs
                        await self._update_retry_count(post_id)
                        continue

                    if create_resp.status_code != 200:
                        error_msg = create_data.get("error", {}).get("message", "Unknown API error")
                        last_error = f"Media creation failed: {error_msg}"
                        logger.error("Instagram media creation failed: %s", last_error)
                        if attempt < MAX_RETRIES:
                            delay = min(RETRY_BASE_DELAY * (2 ** (attempt - 1)), RETRY_MAX_DELAY)
                            await asyncio.sleep(delay)
                            await self._update_retry_count(post_id)
                            continue
                        return PublishResult(
                            success=False,
                            status="failed",
                            failure_reason=last_error,
                        )

                    creation_id = create_data.get("id")
                    if not creation_id:
                        return PublishResult(
                            success=False,
                            status="failed",
                            failure_reason="No creation ID in response",
                        )

                    # Step 2: Publish the media container
                    publish_payload = {
                        "creation_id": creation_id,
                        "access_token": access_token,
                    }
                    publish_resp = await client.post(
                        f"https://graph.facebook.com/v18.0/{ig_user_id}/media_publish",
                        json=publish_payload,
                    )
                    publish_data = publish_resp.json()

                    if publish_resp.status_code == 429:
                        delay = min(RETRY_BASE_DELAY * (2 ** (attempt - 1)), RETRY_MAX_DELAY)
                        logger.warning("Rate limited on publish for post %s. Retrying in %ds", post_id, delay)
                        await asyncio.sleep(delay)
                        await self._update_retry_count(post_id)
                        continue

                    if publish_resp.status_code != 200:
                        error_msg = publish_data.get("error", {}).get("message", "Unknown publish error")
                        last_error = f"Publish failed: {error_msg}"
                        logger.error("Instagram publish failed: %s", last_error)
                        if attempt < MAX_RETRIES:
                            delay = min(RETRY_BASE_DELAY * (2 ** (attempt - 1)), RETRY_MAX_DELAY)
                            await asyncio.sleep(delay)
                            await self._update_retry_count(post_id)
                            continue
                        return PublishResult(
                            success=False,
                            status="failed",
                            failure_reason=last_error,
                        )

                    # Success!
                    platform_post_id = publish_data.get("id", creation_id)
                    permalink = f"https://www.instagram.com/p/{platform_post_id}/"
                    return PublishResult(
                        success=True,
                        status="published",
                        platform_post_id=platform_post_id,
                        platform_permalink=permalink,
                    )

            except httpx.TimeoutException:
                last_error = "Request timed out"
                logger.warning("Timeout on attempt %d/%d for post %s", attempt, MAX_RETRIES, post_id)
                if attempt < MAX_RETRIES:
                    delay = min(RETRY_BASE_DELAY * (2 ** (attempt - 1)), RETRY_MAX_DELAY)
                    await asyncio.sleep(delay)
                    await self._update_retry_count(post_id)
                    continue
            except Exception as exc:
                last_error = str(exc)
                logger.error("Publish error on attempt %d/%d: %s", attempt, MAX_RETRIES, exc)
                if attempt < MAX_RETRIES:
                    delay = min(RETRY_BASE_DELAY * (2 ** (attempt - 1)), RETRY_MAX_DELAY)
                    await asyncio.sleep(delay)
                    await self._update_retry_count(post_id)
                    continue

        return PublishResult(
            success=False,
            status="failed",
            failure_reason=f"All {MAX_RETRIES} attempts failed: {last_error}",
        )

    async def _update_retry_count(self, post_id: str) -> None:
        """Increment the retry count in scheduler_jobs for the post."""
        try:
            from app.core.database import get_supabase_service_client

            supabase = get_supabase_service_client()
            # Try to find and update the existing job record
            job_resp = (
                supabase.table("scheduler_jobs")
                .select("*")
                .eq("post_id", post_id)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            if job_resp.data:
                current_count = job_resp.data[0].get("retry_count", 0)
                supabase.table("scheduler_jobs").update({
                    "retry_count": current_count + 1,
                    "status": "retrying",
                }).eq("id", job_resp.data[0]["id"]).execute()
        except Exception as exc:
            logger.warning("Failed to update retry count for post %s: %s", post_id, exc)

    async def run(self, **kwargs) -> object:
        task = kwargs.get("task", "schedule")
        if task == "schedule":
            return await self.schedule_post(
                post_id=kwargs.get("post_id", ""),
                scheduled_for=kwargs.get("scheduled_for"),
            )
        if task == "cancel":
            return await self.cancel_post(post_id=kwargs.get("post_id", ""))
        if task == "publish":
            return await self.publish_post(post_id=kwargs.get("post_id", ""))
        if task == "retry":
            return await self.retry_failed(post_id=kwargs.get("post_id", ""))
        raise ValueError(f"Unknown task: {task}")
