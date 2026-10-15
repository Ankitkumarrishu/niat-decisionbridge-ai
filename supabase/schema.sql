-- NIAT DecisionBridge AI — Supabase schema
-- Run in Supabase SQL Editor. Enable extensions first.

CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Verified knowledge base (server-managed; counsellors read-only via API)
CREATE TABLE IF NOT EXISTS knowledge_documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  category TEXT NOT NULL,
  content TEXT NOT NULL,
  source_url TEXT NOT NULL,
  last_verified_date DATE NOT NULL,
  verification_status TEXT NOT NULL CHECK (verification_status IN ('verified', 'pending', 'expired')),
  campus_or_university_id TEXT,
  search_vector tsvector GENERATED ALWAYS AS (
    setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(category, '')), 'B') ||
    setweight(to_tsvector('english', coalesce(content, '')), 'C')
  ) STORED,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_knowledge_search ON knowledge_documents USING GIN (search_vector);
CREATE INDEX IF NOT EXISTS idx_knowledge_status ON knowledge_documents (verification_status);

CREATE TABLE IF NOT EXISTS leads (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  student_first_name TEXT NOT NULL,
  email TEXT,
  education_status TEXT NOT NULL,
  preferred_location TEXT,
  preferred_campus TEXT,
  budget_range TEXT NOT NULL,
  primary_concern TEXT NOT NULL,
  additional_question TEXT,
  preferred_language TEXT NOT NULL CHECK (preferred_language IN ('en', 'hi')),
  consent_storage BOOLEAN NOT NULL DEFAULT false,
  consent_storage_at TIMESTAMPTZ,
  consent_followup BOOLEAN NOT NULL DEFAULT false,
  consent_followup_at TIMESTAMPTZ,
  follow_up_status TEXT NOT NULL DEFAULT 'new' CHECK (follow_up_status IN (
    'new', 'brief_generated', 'follow_up_requested', 'contacted', 'application_completed', 'closed'
  )),
  application_status TEXT NOT NULL DEFAULT 'not_started' CHECK (application_status IN (
    'not_started', 'in_progress', 'completed', 'withdrawn'
  )),
  latest_decision_brief_id UUID,
  primary_objection TEXT,
  is_demo BOOLEAN NOT NULL DEFAULT false,
  -- Experiment tracking (Track B pilot)
  experiment_group TEXT CHECK (experiment_group IN ('control', 'treatment')),
  experiment_enrolled_at TIMESTAMPTZ,
  is_eligible_lead BOOLEAN NOT NULL DEFAULT true,
  brief_generated_at TIMESTAMPTZ,
  application_completed_at TIMESTAMPTZ,
  source_identifier TEXT,
  campaign_identifier TEXT,
  counsellor_notes TEXT,
  next_action TEXT
);

CREATE TABLE IF NOT EXISTS decision_briefs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  summary TEXT NOT NULL,
  student_goals JSONB NOT NULL DEFAULT '[]'::jsonb,
  verified_facts JSONB NOT NULL DEFAULT '[]'::jsonb,
  source_references JSONB NOT NULL DEFAULT '[]'::jsonb,
  primary_objection TEXT,
  unresolved_questions JSONB NOT NULL DEFAULT '[]'::jsonb,
  questions_to_ask_counsellor JSONB NOT NULL DEFAULT '[]'::jsonb,
  recommended_next_step TEXT NOT NULL,
  language TEXT NOT NULL,
  verification_notice TEXT NOT NULL,
  generation_status TEXT NOT NULL DEFAULT 'success' CHECK (generation_status IN ('success', 'failed')),
  raw_model_response JSONB
);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_leads_latest_brief'
  ) THEN
    ALTER TABLE leads
      ADD CONSTRAINT fk_leads_latest_brief
      FOREIGN KEY (latest_decision_brief_id) REFERENCES decision_briefs(id) ON DELETE SET NULL;
  END IF;
END $$;

CREATE TABLE IF NOT EXISTS lead_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  event_type TEXT NOT NULL,
  payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_by TEXT
);

CREATE INDEX IF NOT EXISTS idx_leads_created ON leads (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_leads_follow_up ON leads (follow_up_status);
CREATE INDEX IF NOT EXISTS idx_leads_concern ON leads (primary_concern);
CREATE INDEX IF NOT EXISTS idx_leads_demo ON leads (is_demo);
CREATE INDEX IF NOT EXISTS idx_briefs_lead ON decision_briefs (lead_id);
CREATE INDEX IF NOT EXISTS idx_events_lead ON lead_events (lead_id, created_at DESC);

-- RLS: service role (backend) bypasses policies. Browser clients use the anon key
-- only for Supabase Auth, never for direct table access.
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE decision_briefs ENABLE ROW LEVEL SECURITY;
ALTER TABLE lead_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_documents ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Counsellors read leads" ON leads;
DROP POLICY IF EXISTS "Counsellors update leads" ON leads;
DROP POLICY IF EXISTS "Counsellors read briefs" ON decision_briefs;
DROP POLICY IF EXISTS "Counsellors read events" ON lead_events;
DROP POLICY IF EXISTS "Counsellors insert events" ON lead_events;
DROP POLICY IF EXISTS "Counsellors read knowledge" ON knowledge_documents;

REVOKE ALL ON TABLE leads FROM anon, authenticated, PUBLIC;
REVOKE ALL ON TABLE decision_briefs FROM anon, authenticated, PUBLIC;
REVOKE ALL ON TABLE lead_events FROM anon, authenticated, PUBLIC;
REVOKE ALL ON TABLE knowledge_documents FROM anon, authenticated, PUBLIC;

GRANT ALL ON TABLE leads TO service_role;
GRANT ALL ON TABLE decision_briefs TO service_role;
GRANT ALL ON TABLE lead_events TO service_role;
GRANT ALL ON TABLE knowledge_documents TO service_role;

-- No policies for anon/authenticated: unauthenticated clients cannot read leads.
-- Counsellor CRM and dashboard go through FastAPI with JWT + COUNSELLOR_EMAILS.

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS leads_updated_at ON leads;
CREATE TRIGGER leads_updated_at
  BEFORE UPDATE ON leads
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();
