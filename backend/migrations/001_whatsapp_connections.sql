-- WhatsApp Connections table (Option B: separate table with RLS)
-- Run this in Supabase SQL Editor

-- 1. Create table
CREATE TABLE whatsapp_connections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    profile_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    phone_hash TEXT NOT NULL,           -- SHA-256 of normalized phone (for lookup/verification)
    phone_encrypted TEXT NOT NULL,      -- Fernet-encrypted (for sending webhooks if needed)
    wa_business_account_id TEXT,        -- Meta Business Account ID (opaque)
    wa_phone_number_id TEXT,            -- Meta Phone Number ID (opaque)
    verified_at TIMESTAMPTZ,
    status TEXT CHECK (status IN ('pending','verified','revoked')) DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (profile_id)  -- One WhatsApp connection per profile
);

-- 2. Index for lookup by hash
CREATE INDEX idx_whatsapp_connections_phone_hash ON whatsapp_connections(phone_hash);

-- 3. Enable RLS
ALTER TABLE whatsapp_connections ENABLE ROW LEVEL SECURITY;

-- 4. Policy: Users can only access their own WhatsApp connection
CREATE POLICY "own_whatsapp_connection" ON whatsapp_connections
    FOR ALL USING (
        profile_id IN (
            SELECT id FROM profiles WHERE user_id = auth.uid()
        )
    );

-- 5. Trigger to auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_whatsapp_connections_updated_at
    BEFORE UPDATE ON whatsapp_connections
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 6. Remove old column from profiles (if exists)
ALTER TABLE profiles DROP COLUMN IF EXISTS whatsapp_phone;
