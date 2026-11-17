CREATE TABLE IF NOT EXISTS logai_order_orchestration_runs (
  id uuid PRIMARY KEY,
  tenant_id text NOT NULL,
  site_id text NOT NULL,
  business_date date NOT NULL,
  ai_mode text NOT NULL CHECK (ai_mode IN ('suggest', 'supervise', 'sentient')),
  status text NOT NULL,
  source_state jsonb NOT NULL DEFAULT '{}'::jsonb,
  orchestration_state jsonb NOT NULL DEFAULT '{}'::jsonb,
  agentic_result jsonb NOT NULL DEFAULT '{}'::jsonb,
  teams_state jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS logai_order_orchestration_runs_lookup_idx
  ON logai_order_orchestration_runs (tenant_id, site_id, business_date, created_at DESC);

CREATE INDEX IF NOT EXISTS logai_order_orchestration_runs_state_gin_idx
  ON logai_order_orchestration_runs USING gin (orchestration_state);
