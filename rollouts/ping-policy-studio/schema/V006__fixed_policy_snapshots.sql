-- Fixed licensed catalogue + normalized editable content + snapshot usage intervals.
-- No customer operating values or sample content inserted. Existing data retained.
ALTER TABLE logai_policies DROP CONSTRAINT IF EXISTS logai_policies_use_case_check;
ALTER TABLE logai_policies ADD CONSTRAINT logai_policies_use_case_check CHECK(use_case IN ('chute_allocation','order_release','order_orchestration'));
ALTER TABLE logai_snapshot_members DROP CONSTRAINT IF EXISTS logai_snapshot_members_use_case_check;
ALTER TABLE logai_snapshot_members ADD CONSTRAINT logai_snapshot_members_use_case_check CHECK(use_case IN ('chute_allocation','order_release','order_orchestration'));
ALTER TABLE logai_policy_versions DROP CONSTRAINT IF EXISTS logai_policy_versions_backend_check;
ALTER TABLE logai_policy_versions ADD CONSTRAINT logai_policy_versions_backend_check CHECK(backend IN ('postgres','s3','json','relational'));
ALTER TABLE logai_policy_versions DROP CONSTRAINT IF EXISTS lifecycle_payload;
ALTER TABLE logai_policy_versions ADD CONSTRAINT lifecycle_payload CHECK(
 (backend='postgres' AND yaml_text IS NOT NULL AND content_json IS NULL AND object_key IS NULL AND object_version_id IS NULL)
 OR (backend='s3' AND yaml_text IS NULL AND content_json IS NULL AND object_key IS NOT NULL AND object_version_id IS NOT NULL AND object_version_id<>'null')
 OR (backend='json' AND content_json IS NOT NULL AND jsonb_typeof(content_json)='object' AND yaml_text IS NULL AND object_key IS NULL AND object_version_id IS NULL)
 OR (backend='relational' AND content_json IS NULL AND yaml_text IS NULL AND object_key IS NULL AND object_version_id IS NULL));
CREATE TABLE IF NOT EXISTS logai_policy_settings (
 policy_id text NOT NULL, revision bigint NOT NULL, section text NOT NULL CHECK(section IN ('configuration','settings')),
 stable_key text NOT NULL, position integer NOT NULL CHECK(position>=0), label text NOT NULL,
 value_type text NOT NULL CHECK(value_type IN ('text','integer','boolean','null')),
 text_value text, integer_value bigint, boolean_value boolean,
 PRIMARY KEY(policy_id,revision,section,stable_key), UNIQUE(policy_id,revision,section,position),
 FOREIGN KEY(policy_id,revision) REFERENCES logai_policy_versions(policy_id,revision),
 CHECK((value_type='text' AND text_value IS NOT NULL AND integer_value IS NULL AND boolean_value IS NULL)
 OR (value_type='integer' AND integer_value IS NOT NULL AND text_value IS NULL AND boolean_value IS NULL)
 OR (value_type='boolean' AND boolean_value IS NOT NULL AND text_value IS NULL AND integer_value IS NULL)
 OR (value_type='null' AND text_value IS NULL AND integer_value IS NULL AND boolean_value IS NULL))
);
CREATE TABLE IF NOT EXISTS logai_policy_rules (
 policy_id text NOT NULL, revision bigint NOT NULL, rule_id text NOT NULL, position integer NOT NULL,
 statement text NOT NULL, enabled boolean NOT NULL,
 PRIMARY KEY(policy_id,revision,rule_id), UNIQUE(policy_id,revision,position),
 FOREIGN KEY(policy_id,revision) REFERENCES logai_policy_versions(policy_id,revision)
);
CREATE TABLE IF NOT EXISTS logai_policy_objectives (
 policy_id text NOT NULL, revision bigint NOT NULL, objective_id text NOT NULL, position integer NOT NULL,
 statement text NOT NULL, priority text NOT NULL CHECK(priority IN ('undecided','critical','high','medium','low')),
 PRIMARY KEY(policy_id,revision,objective_id), UNIQUE(policy_id,revision,position),
 FOREIGN KEY(policy_id,revision) REFERENCES logai_policy_versions(policy_id,revision)
);
CREATE TABLE IF NOT EXISTS logai_policy_categories (
 policy_id text NOT NULL, revision bigint NOT NULL, category_id text NOT NULL, position integer NOT NULL,
 name text NOT NULL, default_strategy_id text,
 PRIMARY KEY(policy_id,revision,category_id), UNIQUE(policy_id,revision,position),
 FOREIGN KEY(policy_id,revision) REFERENCES logai_policy_versions(policy_id,revision)
);
CREATE TABLE IF NOT EXISTS logai_policy_strategies (
 policy_id text NOT NULL, revision bigint NOT NULL, category_id text NOT NULL, strategy_id text NOT NULL,
 position integer NOT NULL, name text NOT NULL, description text NOT NULL,
 PRIMARY KEY(policy_id,revision,category_id,strategy_id), UNIQUE(policy_id,revision,category_id,position),
 FOREIGN KEY(policy_id,revision,category_id) REFERENCES logai_policy_categories(policy_id,revision,category_id)
);
DO $$ BEGIN
 IF NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conname='policy_category_default' AND conrelid='logai_policy_categories'::regclass) THEN
 ALTER TABLE logai_policy_categories ADD CONSTRAINT policy_category_default FOREIGN KEY(policy_id,revision,category_id,default_strategy_id)
 REFERENCES logai_policy_strategies(policy_id,revision,category_id,strategy_id) DEFERRABLE INITIALLY DEFERRED;
 END IF;
END $$;
DO $$ DECLARE t text; BEGIN
 FOREACH t IN ARRAY ARRAY['logai_policy_settings','logai_policy_rules','logai_policy_objectives','logai_policy_categories','logai_policy_strategies'] LOOP
 EXECUTE format('DROP TRIGGER IF EXISTS normalized_immutable ON %I',t);
 EXECUTE format('CREATE TRIGGER normalized_immutable BEFORE UPDATE OR DELETE ON %I FOR EACH ROW EXECUTE FUNCTION logai_policy_immutable()',t);
 EXECUTE format('DROP TRIGGER IF EXISTS normalized_insert ON %I',t);
 EXECUTE format('CREATE TRIGGER normalized_insert BEFORE INSERT ON %I FOR EACH ROW EXECUTE FUNCTION logai_dictionary_insert_guard()',t);
 END LOOP;
END $$;
-- Fixed slots only for new identities. Legacy arbitrary IDs are retained read-only.
CREATE OR REPLACE FUNCTION logai_policy_catalogue_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF NOT ((NEW.id='sample_chute_allocation' AND NEW.classification='SAMPLE' AND NEW.use_case='chute_allocation')
 OR (NEW.id='chute-allocation' AND NEW.classification='CUSTOMER' AND NEW.use_case='chute_allocation')
 OR (NEW.id='order-release' AND NEW.classification='CUSTOMER' AND NEW.use_case='order_release')
 OR (NEW.id='order-orchestration' AND NEW.classification='CUSTOMER' AND NEW.use_case='order_orchestration')) THEN
 RAISE EXCEPTION 'Policy products require managed provisioning' USING ERRCODE='23514'; END IF;
 RETURN NEW;
END; $$;
DROP TRIGGER IF EXISTS fixed_policy_catalogue ON logai_policies;
CREATE TRIGGER fixed_policy_catalogue BEFORE INSERT ON logai_policies FOR EACH ROW EXECUTE FUNCTION logai_policy_catalogue_guard();
CREATE OR REPLACE FUNCTION logai_complete_snapshot_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF (SELECT count(*) FROM logai_snapshot_members WHERE snapshot_id=NEW.id AND
 ((use_case='chute_allocation' AND policy_id='chute-allocation') OR (use_case='order_release' AND policy_id='order-release') OR (use_case='order_orchestration' AND policy_id='order-orchestration')))<>3
 OR (SELECT count(*) FROM logai_snapshot_members WHERE snapshot_id=NEW.id)<>3 THEN
 RAISE EXCEPTION 'Snapshot requires exactly the three licensed customer policies' USING ERRCODE='23514'; END IF;
 RETURN NEW;
END; $$;
CREATE OR REPLACE FUNCTION logai_current_snapshot_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF (SELECT count(*) FROM logai_snapshot_members WHERE snapshot_id=NEW.snapshot_id AND
 ((use_case='chute_allocation' AND policy_id='chute-allocation') OR (use_case='order_release' AND policy_id='order-release') OR (use_case='order_orchestration' AND policy_id='order-orchestration')))<>3 THEN
 RAISE EXCEPTION 'Snapshot requires the three licensed policies' USING ERRCODE='23514'; END IF;
 RETURN NEW;
END; $$;
CREATE TABLE IF NOT EXISTS logai_policy_snapshot_uses (
 id uuid PRIMARY KEY, snapshot_id uuid NOT NULL REFERENCES logai_global_snapshots(id),
 started_by text NOT NULL, started_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 ended_at timestamptz, closed_by text, request_key text UNIQUE NOT NULL, request_hash char(64) NOT NULL,
 CHECK(ended_at IS NULL OR ended_at>=started_at), CHECK((ended_at IS NULL)=(closed_by IS NULL))
);
CREATE UNIQUE INDEX IF NOT EXISTS one_open_policy_snapshot_use ON logai_policy_snapshot_uses((true)) WHERE ended_at IS NULL;
CREATE OR REPLACE FUNCTION logai_snapshot_use_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF TG_OP='DELETE' OR (to_jsonb(NEW)-'ended_at'-'closed_by') IS DISTINCT FROM (to_jsonb(OLD)-'ended_at'-'closed_by')
 OR OLD.ended_at IS NOT NULL OR NEW.ended_at IS NULL THEN
 RAISE EXCEPTION 'Snapshot use is immutable except its single closure' USING ERRCODE='23514'; END IF;
 RETURN NEW;
END; $$;
DROP TRIGGER IF EXISTS snapshot_use_immutable ON logai_policy_snapshot_uses;
CREATE TRIGGER snapshot_use_immutable BEFORE UPDATE OR DELETE ON logai_policy_snapshot_uses FOR EACH ROW EXECUTE FUNCTION logai_snapshot_use_guard();
-- Pointer is a compatibility projection. New changes must match the one open use.
CREATE OR REPLACE FUNCTION logai_active_snapshot_consistency() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF (SELECT snapshot_id FROM logai_current_snapshot WHERE singleton=true) IS DISTINCT FROM
 (SELECT snapshot_id FROM logai_policy_snapshot_uses WHERE ended_at IS NULL) THEN
 RAISE EXCEPTION 'Current snapshot must match its open usage period' USING ERRCODE='23514'; END IF;
 RETURN NULL;
END; $$;
DROP TRIGGER IF EXISTS snapshot_use_consistency ON logai_policy_snapshot_uses;
CREATE CONSTRAINT TRIGGER snapshot_use_consistency AFTER INSERT OR UPDATE OR DELETE ON logai_policy_snapshot_uses DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION logai_active_snapshot_consistency();
DROP TRIGGER IF EXISTS snapshot_pointer_consistency ON logai_current_snapshot;
CREATE CONSTRAINT TRIGGER snapshot_pointer_consistency AFTER INSERT OR UPDATE OR DELETE ON logai_current_snapshot DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION logai_active_snapshot_consistency();
CREATE TABLE IF NOT EXISTS logai_snapshot_approvals (
 id uuid PRIMARY KEY, snapshot_id uuid NOT NULL REFERENCES logai_global_snapshots(id),
 reviewer text NOT NULL, created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 consumed_use uuid REFERENCES logai_policy_snapshot_uses(id)
);
CREATE OR REPLACE FUNCTION logai_snapshot_approval_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF TG_OP='DELETE' OR (to_jsonb(NEW)-'consumed_use') IS DISTINCT FROM (to_jsonb(OLD)-'consumed_use')
 OR OLD.consumed_use IS NOT NULL OR NEW.consumed_use IS NULL THEN
 RAISE EXCEPTION 'Snapshot approval is immutable and single-use' USING ERRCODE='23514'; END IF;
 RETURN NEW;
END; $$;
DROP TRIGGER IF EXISTS snapshot_approval_immutable ON logai_snapshot_approvals;
CREATE TRIGGER snapshot_approval_immutable BEFORE UPDATE OR DELETE ON logai_snapshot_approvals FOR EACH ROW EXECUTE FUNCTION logai_snapshot_approval_guard();

CREATE OR REPLACE FUNCTION logai_snapshot_member_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF NOT EXISTS(SELECT 1 FROM logai_policies p JOIN logai_policy_versions v ON v.policy_id=p.id
 WHERE p.id=NEW.policy_id AND v.revision=NEW.revision AND p.classification='CUSTOMER'
 AND p.use_case=NEW.use_case AND v.backend='relational' AND v.validation->>'valid'='true' AND v.checksum=NEW.fingerprint
 AND p.id IN ('chute-allocation','order-release','order-orchestration')) THEN
 RAISE EXCEPTION 'Snapshot member must be a valid licensed customer version' USING ERRCODE='23514'; END IF;
 IF NOT EXISTS(SELECT 1 FROM logai_global_snapshots WHERE id=NEW.snapshot_id AND xmin::text::bigint=txid_current()%4294967296) THEN
 RAISE EXCEPTION 'Snapshot membership is immutable after creation' USING ERRCODE='23514'; END IF;
 RETURN NEW;
END; $$;
