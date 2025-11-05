-- SQL Migration: Add Multi-Tenant Support to Stellar Sales System
-- Date: October 23, 2025
-- Purpose: Enable user accounts, organizations, and team features for DemoDesk-like functionality

-- ===============================================
-- 1. ORGANIZATIONS TABLE
-- ===============================================
CREATE TABLE IF NOT EXISTS organizations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL, -- URL-friendly name (e.g., "acme-corp")
    plan VARCHAR(50) DEFAULT 'free', -- free, pro, enterprise
    max_users INTEGER DEFAULT 5, -- User limit per plan
    max_transcripts_per_month INTEGER DEFAULT 100, -- Usage limits
    
    -- Subscription details
    stripe_customer_id VARCHAR(255), -- For billing integration
    subscription_status VARCHAR(50) DEFAULT 'trial', -- trial, active, canceled, past_due
    trial_ends_at TIMESTAMP,
    subscription_ends_at TIMESTAMP,
    
    -- Settings
    settings JSONB DEFAULT '{}', -- Org-specific config (theme, logo, etc.)
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP -- Soft delete for GDPR compliance
);

-- Index for fast lookups
CREATE INDEX idx_organizations_slug ON organizations(slug);
CREATE INDEX idx_organizations_subscription ON organizations(subscription_status);

-- ===============================================
-- 2. USERS TABLE
-- ===============================================
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL, -- bcrypt hash
    full_name VARCHAR(255),
    avatar_url TEXT, -- Profile picture URL
    
    -- Role-based access control
    role VARCHAR(50) DEFAULT 'rep', -- admin, manager, rep
    org_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Authentication
    email_verified BOOLEAN DEFAULT FALSE,
    email_verification_token VARCHAR(255),
    password_reset_token VARCHAR(255),
    password_reset_expires_at TIMESTAMP,
    
    -- Session management
    last_login_at TIMESTAMP,
    last_login_ip VARCHAR(45), -- IPv6-compatible
    
    -- Integrations
    zoom_access_token TEXT, -- Encrypted Zoom OAuth token
    zoom_refresh_token TEXT,
    zoom_token_expires_at TIMESTAMP,
    
    google_meet_access_token TEXT,
    google_meet_refresh_token TEXT,
    
    -- Preferences
    preferences JSONB DEFAULT '{}', -- UI settings, notifications, etc.
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP -- Soft delete
);

-- Indexes for performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_org_id ON users(org_id);
CREATE INDEX idx_users_role ON users(role);

-- ===============================================
-- 3. MEETING SESSIONS TABLE
-- ===============================================
CREATE TABLE IF NOT EXISTS meeting_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    org_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
    transcript_id INTEGER REFERENCES transcripts(id) ON DELETE SET NULL,
    
    -- Meeting details
    meeting_platform VARCHAR(50), -- zoom, google_meet, microsoft_teams
    meeting_platform_id VARCHAR(255), -- Platform-specific meeting ID
    meeting_title VARCHAR(500),
    meeting_url TEXT,
    
    -- Participants
    host_email VARCHAR(255),
    participants JSONB DEFAULT '[]', -- [{"name": "John", "email": "john@example.com"}]
    participant_count INTEGER DEFAULT 0,
    
    -- Status tracking
    status VARCHAR(50) DEFAULT 'scheduled', -- scheduled, in_progress, completed, failed, canceled
    
    -- Recording details
    recording_url TEXT,
    recording_downloaded BOOLEAN DEFAULT FALSE,
    recording_size_bytes BIGINT,
    
    -- Transcript processing
    transcript_processed BOOLEAN DEFAULT FALSE,
    transcript_processing_started_at TIMESTAMP,
    transcript_processing_completed_at TIMESTAMP,
    
    -- AI suggestions generated during meeting
    suggestions_count INTEGER DEFAULT 0,
    
    -- Timestamps
    scheduled_at TIMESTAMP,
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    duration_seconds INTEGER,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_meeting_sessions_user ON meeting_sessions(user_id);
CREATE INDEX idx_meeting_sessions_org ON meeting_sessions(org_id);
CREATE INDEX idx_meeting_sessions_status ON meeting_sessions(status);
CREATE INDEX idx_meeting_sessions_platform ON meeting_sessions(meeting_platform);
CREATE INDEX idx_meeting_sessions_started ON meeting_sessions(started_at);

-- ===============================================
-- 4. AI SUGGESTIONS TABLE (Real-Time Assistant)
-- ===============================================
CREATE TABLE IF NOT EXISTS suggestions (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES meeting_sessions(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    
    -- Suggestion metadata
    suggestion_type VARCHAR(50), -- battlecard, objection_handling, next_step, closing_technique
    trigger_phrase TEXT, -- What the client said that triggered this
    suggestion_text TEXT NOT NULL, -- The actual suggestion content
    confidence_score FLOAT CHECK (confidence_score >= 0 AND confidence_score <= 1),
    
    -- Context
    conversation_phase VARCHAR(100), -- e.g., "price negotiation", "objection handling"
    timestamp_in_meeting INTEGER, -- Seconds from meeting start
    
    -- User interaction
    shown_to_user BOOLEAN DEFAULT TRUE,
    user_clicked BOOLEAN DEFAULT FALSE,
    user_dismissed BOOLEAN DEFAULT FALSE,
    user_feedback VARCHAR(50), -- helpful, not_helpful, irrelevant
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    shown_at TIMESTAMP,
    clicked_at TIMESTAMP
);

-- Indexes
CREATE INDEX idx_suggestions_session ON suggestions(session_id);
CREATE INDEX idx_suggestions_type ON suggestions(suggestion_type);
CREATE INDEX idx_suggestions_user ON suggestions(user_id);

-- ===============================================
-- 5. TEAM METRICS TABLE (Analytics)
-- ===============================================
CREATE TABLE IF NOT EXISTS team_metrics (
    id SERIAL PRIMARY KEY,
    org_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE, -- NULL = org-wide metrics
    
    -- Date range
    metric_date DATE NOT NULL, -- Daily metrics
    metric_period VARCHAR(20) DEFAULT 'day', -- day, week, month, quarter
    
    -- Meeting metrics
    total_meetings INTEGER DEFAULT 0,
    completed_meetings INTEGER DEFAULT 0,
    avg_meeting_duration_minutes FLOAT,
    
    -- Deal metrics
    deals_created INTEGER DEFAULT 0,
    deals_won INTEGER DEFAULT 0,
    deals_lost INTEGER DEFAULT 0,
    deals_pending INTEGER DEFAULT 0,
    
    -- Revenue metrics
    total_revenue DECIMAL(12, 2) DEFAULT 0,
    avg_deal_size DECIMAL(12, 2) DEFAULT 0,
    largest_deal DECIMAL(12, 2) DEFAULT 0,
    
    -- Conversion metrics
    win_rate FLOAT, -- deals_won / (deals_won + deals_lost)
    avg_time_to_close_days FLOAT,
    
    -- Activity metrics
    emails_sent INTEGER DEFAULT 0,
    follow_ups_completed INTEGER DEFAULT 0,
    
    -- AI metrics
    suggestions_generated INTEGER DEFAULT 0,
    suggestions_used INTEGER DEFAULT 0,
    avg_suggestion_confidence FLOAT,
    
    -- Coaching metrics
    coaching_sessions_completed INTEGER DEFAULT 0,
    avg_coaching_score FLOAT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_team_metrics_org ON team_metrics(org_id);
CREATE INDEX idx_team_metrics_user ON team_metrics(user_id);
CREATE INDEX idx_team_metrics_date ON team_metrics(metric_date);
CREATE INDEX idx_team_metrics_period ON team_metrics(metric_period);

-- Composite index for common queries
CREATE INDEX idx_team_metrics_org_date ON team_metrics(org_id, metric_date);

-- ===============================================
-- 6. UPDATE EXISTING TRANSCRIPTS TABLE
-- ===============================================
-- Add new columns to link transcripts to users/orgs
ALTER TABLE transcripts 
ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS org_id INTEGER REFERENCES organizations(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS session_id INTEGER REFERENCES meeting_sessions(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS meeting_platform VARCHAR(50),
ADD COLUMN IF NOT EXISTS meeting_url TEXT,
ADD COLUMN IF NOT EXISTS duration_seconds INTEGER,
ADD COLUMN IF NOT EXISTS participants JSONB DEFAULT '[]',
ADD COLUMN IF NOT EXISTS processed_by_agent VARCHAR(100), -- Which AI model processed this
ADD COLUMN IF NOT EXISTS processing_time_seconds FLOAT;

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_transcripts_user ON transcripts(user_id);
CREATE INDEX IF NOT EXISTS idx_transcripts_org ON transcripts(org_id);
CREATE INDEX IF NOT EXISTS idx_transcripts_session ON transcripts(session_id);

-- ===============================================
-- 7. AUDIT LOG TABLE (Enterprise Feature)
-- ===============================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    org_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    
    -- Action details
    action_type VARCHAR(100) NOT NULL, -- login, create_transcript, update_deal, delete_user, etc.
    resource_type VARCHAR(50), -- user, transcript, organization, etc.
    resource_id INTEGER,
    
    -- Request details
    ip_address VARCHAR(45),
    user_agent TEXT,
    request_method VARCHAR(10), -- GET, POST, PUT, DELETE
    request_path VARCHAR(500),
    
    -- Changes (for update actions)
    old_values JSONB,
    new_values JSONB,
    
    -- Outcome
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_audit_logs_org ON audit_logs(org_id);
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action_type);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at);

-- ===============================================
-- 8. INVITATION TABLE (Team Invites)
-- ===============================================
CREATE TABLE IF NOT EXISTS invitations (
    id SERIAL PRIMARY KEY,
    org_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
    invited_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    
    email VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'rep',
    
    token VARCHAR(255) UNIQUE NOT NULL,
    status VARCHAR(50) DEFAULT 'pending', -- pending, accepted, expired
    
    expires_at TIMESTAMP NOT NULL,
    accepted_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_invitations_org ON invitations(org_id);
CREATE INDEX idx_invitations_email ON invitations(email);
CREATE INDEX idx_invitations_token ON invitations(token);

-- ===============================================
-- 9. SEED DATA (Development Only)
-- ===============================================
-- Insert a demo organization
INSERT INTO organizations (name, slug, plan, max_users, subscription_status)
VALUES ('Demo Company', 'demo-company', 'pro', 10, 'active')
ON CONFLICT (slug) DO NOTHING;

-- Insert a demo admin user (password: "password123" - CHANGE THIS!)
-- Hash generated with: bcrypt.hashpw("password123".encode(), bcrypt.gensalt())
INSERT INTO users (email, password_hash, full_name, role, org_id, email_verified)
VALUES (
    'admin@demo.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5lXvV6VHXx7.O', -- password123
    'Demo Admin',
    'admin',
    (SELECT id FROM organizations WHERE slug = 'demo-company'),
    TRUE
)
ON CONFLICT (email) DO NOTHING;

-- ===============================================
-- 10. FUNCTIONS & TRIGGERS
-- ===============================================

-- Function to update 'updated_at' timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to all tables with updated_at
DROP TRIGGER IF EXISTS update_organizations_updated_at ON organizations;
CREATE TRIGGER update_organizations_updated_at
    BEFORE UPDATE ON organizations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_meeting_sessions_updated_at ON meeting_sessions;
CREATE TRIGGER update_meeting_sessions_updated_at
    BEFORE UPDATE ON meeting_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_transcripts_updated_at ON transcripts;
CREATE TRIGGER update_transcripts_updated_at
    BEFORE UPDATE ON transcripts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ===============================================
-- MIGRATION COMPLETE!
-- ===============================================
-- Run this script with:
-- psql -U postgres -d stellar_sales -f sql/add_user_tables.sql

-- Verify tables created:
-- SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;
