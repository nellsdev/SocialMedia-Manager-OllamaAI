"""SQLAlchemy ORM models for all six application tables.

Each table maps to a Supabase PostgreSQL table with the same name. RLS is
scoped via ``profile_id IN (SELECT id FROM profiles WHERE user_id = auth.uid())``.
"""

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


# ---------------------------------------------------------------------------
# Helper column types
# ---------------------------------------------------------------------------

def _uuid_pk() -> Column:
    return Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


def _timestamps() -> tuple[Column, Column]:
    return (
        Column("created_at", DateTime(timezone=True), server_default=func.now()),
        Column("updated_at", DateTime(timezone=True), server_default=func.now(), onupdate=func.now()),
    )


# ---------------------------------------------------------------------------
# profiles
# ---------------------------------------------------------------------------

class Profile(Base):
    __tablename__ = "profiles"

    id = _uuid_pk()
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    name = Column(String(255), nullable=False, default="Personal")
    slug = Column(String(255), unique=True, nullable=False)
    avatar_url = Column(Text, nullable=True)

    # Archetype system
    archetype = Column(
        String(50),
        nullable=False,
        default="personal_sharing",
        comment="ENUM: aspiring_influencer, authority_professional, personal_sharing, business_owner, community_builder",
    )
    voice_description = Column(Text, nullable=True)
    content_pillars = Column(ARRAY(String), nullable=True)
    target_audience = Column(Text, nullable=True)
    goals = Column(Text, nullable=True)
    visual_references = Column(ARRAY(String), nullable=True)
    whatsapp_phone = Column(String(50), nullable=True, comment="Linked WhatsApp number")

    created_at, updated_at = _timestamps()

    # Relationships
    social_accounts = relationship("SocialAccount", back_populates="profile", cascade="all, delete-orphan")
    content_ideas = relationship("ContentIdea", back_populates="profile", cascade="all, delete-orphan")
    content_posts = relationship("ContentPost", back_populates="profile", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Profile {self.slug} ({self.archetype})>"


# ---------------------------------------------------------------------------
# social_accounts
# ---------------------------------------------------------------------------

class SocialAccount(Base):
    __tablename__ = "social_accounts"

    id = _uuid_pk()
    profile_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    platform = Column(String(50), nullable=False, default="instagram")
    account_name = Column(String(255), nullable=False)
    account_id = Column(String(255), nullable=False)
    access_token = Column(Text, nullable=False, comment="Fernet-encrypted")
    refresh_token = Column(Text, nullable=True, comment="Fernet-encrypted")
    token_expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)

    created_at, updated_at = _timestamps()

    # Relationships
    profile = relationship("Profile", back_populates="social_accounts")
    metrics_snapshots = relationship("MetricsSnapshot", back_populates="social_account", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<SocialAccount {self.platform}:{self.account_name}>"


# ---------------------------------------------------------------------------
# content_ideas
# ---------------------------------------------------------------------------

class ContentIdea(Base):
    __tablename__ = "content_ideas"

    id = _uuid_pk()
    profile_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    suggested_format = Column(String(50), nullable=True, comment="story / carousel / reel / live")
    content_pillar = Column(String(100), nullable=True)
    source = Column(String(50), nullable=False, default="manual", comment="manual / whatsapp")
    media_refs = Column(ARRAY(String), nullable=True, comment="URLs from WhatsApp")
    status = Column(String(20), nullable=False, default="idea", comment="idea / converted")
    converted_to = Column(UUID(as_uuid=True), ForeignKey("content_posts.id", ondelete="SET NULL"), nullable=True)

    created_at, updated_at = _timestamps()

    # Relationships
    profile = relationship("Profile", back_populates="content_ideas")

    def __repr__(self) -> str:
        return f"<ContentIdea {self.title!r} [{self.status}]>"


# ---------------------------------------------------------------------------
# content_posts
# ---------------------------------------------------------------------------

class ContentPost(Base):
    __tablename__ = "content_posts"

    id = _uuid_pk()
    profile_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    ig_account_id = Column(UUID(as_uuid=True), ForeignKey("social_accounts.id", ondelete="SET NULL"), nullable=True)
    format = Column(String(50), nullable=False, comment="story / carousel / reel / live")
    title = Column(String(255), nullable=True)
    caption = Column(Text, nullable=True)
    first_comment = Column(Text, nullable=True)
    media_urls = Column(ARRAY(String), nullable=True)
    hashtags = Column(ARRAY(String), nullable=True)
    status = Column(String(20), nullable=False, default="draft", comment="draft / scheduled / published / failed / retrying")
    scheduled_for = Column(DateTime(timezone=True), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    platform_post_id = Column(String(255), nullable=True)
    platform_permalink = Column(Text, nullable=True)
    failure_reason = Column(Text, nullable=True)

    created_at, updated_at = _timestamps()

    # Relationships
    profile = relationship("Profile", back_populates="content_posts")

    def __repr__(self) -> str:
        return f"<ContentPost {self.title!r} [{self.format}] [{self.status}]>"


# ---------------------------------------------------------------------------
# metrics_snapshots
# ---------------------------------------------------------------------------

class MetricsSnapshot(Base):
    __tablename__ = "metrics_snapshots"

    id = _uuid_pk()
    social_account_id = Column(UUID(as_uuid=True), ForeignKey("social_accounts.id", ondelete="CASCADE"), nullable=False)
    metric_date = Column(Date, nullable=False, default=date.today)
    followers = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    reach = Column(Integer, default=0)
    saves = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    engagement_rate = Column(Float, default=0.0)
    raw_data = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    social_account = relationship("SocialAccount", back_populates="metrics_snapshots")

    def __repr__(self) -> str:
        return f"<MetricsSnapshot {self.metric_date} (eng:{self.engagement_rate})>"


# ---------------------------------------------------------------------------
# scheduler_jobs
# ---------------------------------------------------------------------------

class SchedulerJob(Base):
    __tablename__ = "scheduler_jobs"

    id = _uuid_pk()
    post_id = Column(UUID(as_uuid=True), ForeignKey("content_posts.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(String(255), nullable=False, comment="APScheduler job ID")
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(20), nullable=False, default="pending", comment="pending / running / completed / failed")
    retry_count = Column(Integer, default=0)

    created_at, updated_at = _timestamps()

    def __repr__(self) -> str:
        return f"<SchedulerJob post={self.post_id} [{self.status}]>"
