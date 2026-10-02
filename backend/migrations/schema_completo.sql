-- ============================================================================
-- SOCIAL MEDIA MANAGER - Complete Database Schema
-- Run this in Supabase Dashboard → SQL Editor (single execution)
-- ============================================================================
-- Tables: profiles, social_accounts, content_ideas, content_posts,
--         metrics_snapshots, scheduler_jobs, whatsapp_connections
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 0. Extensions & Helpers
-- ----------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Helper function for updated_at triggers
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ----------------------------------------------------------------------------
-- 1. PROFILES
-- ----------------------------------------------------------------------------
CREATE TABLE profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    name TEXT NOT NULL DEFAULT 'Personal',
    slug TEXT UNIQUE NOT NULL DEFAULT 'personal',
    avatar_url TEXT,
    -- Archetype system
    archetype TEXT CHECK (archetype IN (
        'aspiring_influencer',
        'authority_professional',
        'personal_sharing',
        'business_owner',
        'community_builder'
    )) DEFAULT 'personal_sharing',
    voice_description TEXT,
    content_pillars TEXT[],
    target_audience TEXT,
    goals TEXT,
    visual_references TEXT[],
    niche TEXT,
    niche_analysis JSONB,
    language TEXT DEFAULT 'español',
    aesthetic_description TEXT,
    brand_colors TEXT[],
    visual_style TEXT,
    brand_starter JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_profiles_user_id ON profiles(user_id);
CREATE INDEX idx_profiles_slug ON profiles(slug);

ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "own_profile" ON profiles
    FOR ALL USING (auth.uid() = user_id);

CREATE TRIGGER update_profiles_updated_at
    BEFORE UPDATE ON profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ----------------------------------------------------------------------------
-- 2. SOCIAL ACCOUNTS (Instagram, etc.)
-- ----------------------------------------------------------------------------
CREATE TABLE social_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    profile_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
    platform TEXT NOT NULL CHECK (platform = 'instagram'),
    account_name TEXT NOT NULL,
    account_id TEXT NOT NULL,
    access_token TEXT NOT NULL,          -- Fernet-encrypted
    refresh_token TEXT,                  -- Fernet-encrypted
    token_expires_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_social_accounts_profile_id ON social_accounts(profile_id);
CREATE UNIQUE INDEX idx_social_accounts_platform_account ON social_accounts(platform, account_id);

ALTER TABLE social_accounts ENABLE ROW LEVEL SECURITY;
CREATE POLICY "own_social_accounts" ON social_accounts
    FOR ALL USING (
        profile_id IN (SELECT id FROM profiles WHERE user_id = auth.uid())
    );

CREATE TRIGGER update_social_accounts_updated_at
    BEFORE UPDATE ON social_accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ----------------------------------------------------------------------------
-- 3. CONTENT POSTS (antes que content_ideas para que la FK converted_to resuelva)
-- ----------------------------------------------------------------------------
CREATE TABLE content_posts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    profile_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
    ig_account_id UUID REFERENCES social_accounts(id) ON DELETE SET NULL,
    format TEXT NOT NULL CHECK (format IN ('story','carousel','reel','live')),
    title TEXT,
    caption TEXT,
    first_comment TEXT,
    media_urls TEXT[],
    hashtags TEXT[],
    status TEXT CHECK (status IN ('draft','scheduled','published','failed','retrying')) DEFAULT 'draft',
    scheduled_for TIMESTAMPTZ,
    published_at TIMESTAMPTZ,
    platform_post_id TEXT,
    platform_permalink TEXT,
    failure_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_content_posts_profile_id ON content_posts(profile_id);
CREATE INDEX idx_content_posts_status ON content_posts(status);
CREATE INDEX idx_content_posts_scheduled_for ON content_posts(scheduled_for) WHERE status = 'scheduled';
CREATE INDEX idx_content_posts_ig_account_id ON content_posts(ig_account_id);

ALTER TABLE content_posts ENABLE ROW LEVEL SECURITY;
CREATE POLICY "own_content_posts" ON content_posts
    FOR ALL USING (
        profile_id IN (SELECT id FROM profiles WHERE user_id = auth.uid())
    );

CREATE TRIGGER update_content_posts_updated_at
    BEFORE UPDATE ON content_posts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ----------------------------------------------------------------------------
-- 4. CONTENT IDEAS
-- ----------------------------------------------------------------------------
CREATE TABLE content_ideas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    profile_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    suggested_format TEXT CHECK (suggested_format IN ('story','carousel','reel','live')),
    content_pillar TEXT,
    source TEXT CHECK (source IN ('manual','whatsapp')) DEFAULT 'manual',
    media_refs TEXT[],
    status TEXT CHECK (status IN ('idea','converted')) DEFAULT 'idea',
    converted_to UUID REFERENCES content_posts(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_content_ideas_profile_id ON content_ideas(profile_id);
CREATE INDEX idx_content_ideas_status ON content_ideas(status);
CREATE INDEX idx_content_ideas_pillar ON content_ideas(content_pillar);
CREATE INDEX idx_content_ideas_source ON content_ideas(source);

ALTER TABLE content_ideas ENABLE ROW LEVEL SECURITY;
CREATE POLICY "own_content_ideas" ON content_ideas
    FOR ALL USING (
        profile_id IN (SELECT id FROM profiles WHERE user_id = auth.uid())
    );

CREATE TRIGGER update_content_ideas_updated_at
    BEFORE UPDATE ON content_ideas
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ----------------------------------------------------------------------------
-- 5. METRICS SNAPSHOTS (Daily KPIs per Instagram account)
-- ----------------------------------------------------------------------------
CREATE TABLE metrics_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    social_account_id UUID REFERENCES social_accounts(id) ON DELETE CASCADE NOT NULL,
    metric_date DATE NOT NULL DEFAULT CURRENT_DATE,
    followers INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    reach INTEGER DEFAULT 0,
    saves INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    engagement_rate DECIMAL(5,2) DEFAULT 0.00,
    raw_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (social_account_id, metric_date)
);

CREATE INDEX idx_metrics_snapshots_account_date ON metrics_snapshots(social_account_id, metric_date DESC);

ALTER TABLE metrics_snapshots ENABLE ROW LEVEL SECURITY;
CREATE POLICY "own_metrics_snapshots" ON metrics_snapshots
    FOR ALL USING (
        social_account_id IN (
            SELECT id FROM social_accounts
            WHERE profile_id IN (SELECT id FROM profiles WHERE user_id = auth.uid())
        )
    );

-- ----------------------------------------------------------------------------
-- 6. SCHEDULER JOBS (APScheduler persistence)
-- ----------------------------------------------------------------------------
CREATE TABLE scheduler_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    post_id UUID REFERENCES content_posts(id) ON DELETE CASCADE NOT NULL,
    job_id TEXT NOT NULL,                 -- APScheduler internal job ID
    scheduled_at TIMESTAMPTZ NOT NULL,
    status TEXT CHECK (status IN ('pending','running','completed','failed','retrying')) DEFAULT 'pending',
    retry_count INTEGER DEFAULT 0,
    executed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_scheduler_jobs_post_id ON scheduler_jobs(post_id);
CREATE INDEX idx_scheduler_jobs_scheduled_at ON scheduler_jobs(scheduled_at) WHERE status = 'pending';
CREATE INDEX idx_scheduler_jobs_status ON scheduler_jobs(status);

ALTER TABLE scheduler_jobs ENABLE ROW LEVEL SECURITY;
CREATE POLICY "own_scheduler_jobs" ON scheduler_jobs
    FOR ALL USING (
        post_id IN (
            SELECT id FROM content_posts
            WHERE profile_id IN (SELECT id FROM profiles WHERE user_id = auth.uid())
        )
    );

CREATE TRIGGER update_scheduler_jobs_updated_at
    BEFORE UPDATE ON scheduler_jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ----------------------------------------------------------------------------
-- 7. WHATSAPP CONNECTIONS (Option B: PII-protected)
-- ----------------------------------------------------------------------------
CREATE TABLE whatsapp_connections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    profile_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
    phone_hash TEXT NOT NULL,                    -- SHA-256 of normalized phone
    phone_encrypted TEXT NOT NULL,               -- Fernet-encrypted (for webhooks)
    wa_business_account_id TEXT,                 -- Meta Business Account ID
    wa_phone_number_id TEXT,                     -- Meta Phone Number ID
    verified_at TIMESTAMPTZ,
    status TEXT CHECK (status IN ('pending','verified','revoked')) DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (profile_id)
);

CREATE INDEX idx_whatsapp_connections_phone_hash ON whatsapp_connections(phone_hash);

ALTER TABLE whatsapp_connections ENABLE ROW LEVEL SECURITY;
CREATE POLICY "own_whatsapp_connection" ON whatsapp_connections
    FOR ALL USING (
        profile_id IN (SELECT id FROM profiles WHERE user_id = auth.uid())
    );

CREATE TRIGGER update_whatsapp_connections_updated_at
    BEFORE UPDATE ON whatsapp_connections
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ----------------------------------------------------------------------------
-- 8. AGENT MEMORIES (production memory for agent interactions)
-- ----------------------------------------------------------------------------
CREATE TABLE agent_memories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    profile_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
    agent_type TEXT NOT NULL,
    task TEXT NOT NULL,
    prompt TEXT NOT NULL,
    response TEXT NOT NULL,
    model TEXT,
    latency_ms INTEGER,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_agent_memories_profile ON agent_memories(profile_id, created_at DESC);
CREATE INDEX idx_agent_memories_agent ON agent_memories(profile_id, agent_type, created_at DESC);

ALTER TABLE agent_memories ENABLE ROW LEVEL SECURITY;
CREATE POLICY "own_agent_memories" ON agent_memories
    FOR ALL USING (
        profile_id IN (SELECT id FROM profiles WHERE user_id = auth.uid())
    );

-- ----------------------------------------------------------------------------
-- 9. Onboarding research columns (idempotent for existing deployments)
-- ----------------------------------------------------------------------------
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS niche TEXT;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS niche_analysis JSONB;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS language TEXT DEFAULT 'español';
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS aesthetic_description TEXT;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS brand_colors TEXT[];
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS visual_style TEXT;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS brand_starter JSONB;

-- ----------------------------------------------------------------------------
-- 10. Cleanup: Remove legacy column if exists
-- ----------------------------------------------------------------------------
ALTER TABLE profiles DROP COLUMN IF EXISTS whatsapp_phone;

-- ============================================================================
-- VERIFICATION QUERIES (run after to confirm)
-- ============================================================================
-- SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;
-- SELECT * FROM profiles LIMIT 1;
-- SELECT * FROM whatsapp_connections LIMIT 1;
-- SELECT polname, polcmd FROM pg_policy WHERE polrelid = 'profiles'::regclass;
