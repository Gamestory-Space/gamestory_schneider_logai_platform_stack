CREATE TABLE IF NOT EXISTS logai_release_shipments (
  id uuid PRIMARY KEY,
  tenant_id text NOT NULL,
  site_id text NOT NULL,
  business_date date NOT NULL,
  shipment_id text NOT NULL,
  status text NOT NULL CHECK (status IN ('releasing', 'paused', 'completed')),
  mode text NOT NULL CHECK (mode IN ('auto', 'manual')),
  carrier jsonb NOT NULL DEFAULT '{}'::jsonb,
  transport jsonb NOT NULL DEFAULT '{}'::jsonb,
  schedule jsonb NOT NULL DEFAULT '{}'::jsonb,
  progress jsonb NOT NULL DEFAULT '{}'::jsonb,
  alerts jsonb NOT NULL DEFAULT '[]'::jsonb,
  sort_time time,
  source jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, site_id, business_date, shipment_id)
);

CREATE INDEX IF NOT EXISTS logai_release_shipments_lookup_idx
  ON logai_release_shipments (tenant_id, site_id, business_date, sort_time DESC);

CREATE INDEX IF NOT EXISTS logai_release_shipments_alerts_gin_idx
  ON logai_release_shipments USING gin (alerts);

CREATE TABLE IF NOT EXISTS logai_chutes (
  id uuid PRIMARY KEY,
  tenant_id text NOT NULL,
  site_id text NOT NULL,
  business_date date NOT NULL,
  chute_number integer NOT NULL CHECK (chute_number > 0),
  utilization numeric(5,2) NOT NULL DEFAULT 0,
  capacity jsonb NOT NULL DEFAULT '{}'::jsonb,
  lanes jsonb NOT NULL DEFAULT '[]'::jsonb,
  last_release_time time,
  source jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, site_id, business_date, chute_number)
);

CREATE INDEX IF NOT EXISTS logai_chutes_lookup_idx
  ON logai_chutes (tenant_id, site_id, business_date, last_release_time DESC);

CREATE INDEX IF NOT EXISTS logai_chutes_lanes_gin_idx
  ON logai_chutes USING gin (lanes);
