-- Additive compatibility migration. No seeds, selections or snapshots are inserted.
ALTER TABLE logai_policies ADD COLUMN IF NOT EXISTS classification text NOT NULL DEFAULT 'CUSTOMER' CHECK(classification IN ('SAMPLE','CUSTOMER'));
ALTER TABLE logai_policies ADD COLUMN IF NOT EXISTS use_case text NOT NULL DEFAULT 'chute_allocation' CHECK(use_case='chute_allocation');
ALTER TABLE logai_policies ADD COLUMN IF NOT EXISTS origin_sample text REFERENCES logai_policies(id);
ALTER TABLE logai_policy_versions ADD COLUMN IF NOT EXISTS content_json jsonb;
ALTER TABLE logai_policy_versions ADD COLUMN IF NOT EXISTS content_schema integer NOT NULL DEFAULT 1 CHECK(content_schema=1);
ALTER TABLE logai_policy_versions ADD COLUMN IF NOT EXISTS customer_reviewed boolean NOT NULL DEFAULT false;
ALTER TABLE logai_policy_versions DROP CONSTRAINT IF EXISTS logai_policy_versions_backend_check;
ALTER TABLE logai_policy_versions ADD CONSTRAINT logai_policy_versions_backend_check CHECK(backend IN ('postgres','s3','json','relational'));
ALTER TABLE logai_policy_versions DROP CONSTRAINT IF EXISTS logai_policy_versions_check;
ALTER TABLE logai_policy_versions DROP CONSTRAINT IF EXISTS lifecycle_payload;
ALTER TABLE logai_policy_versions ADD CONSTRAINT lifecycle_payload CHECK(
 (backend='postgres' AND yaml_text IS NOT NULL AND content_json IS NULL AND object_key IS NULL AND object_version_id IS NULL)
 OR (backend='s3' AND yaml_text IS NULL AND content_json IS NULL AND object_key IS NOT NULL AND object_version_id IS NOT NULL AND object_version_id<>'null')
 OR (backend='relational' AND content_json IS NULL AND yaml_text IS NULL AND object_key IS NULL AND object_version_id IS NULL)
 OR (backend='json' AND content_json IS NOT NULL AND jsonb_typeof(content_json)='object' AND yaml_text IS NULL AND object_key IS NULL AND object_version_id IS NULL));
CREATE OR REPLACE FUNCTION logai_policy_identity_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF TG_OP='DELETE' OR OLD.classification='SAMPLE' OR
 (NEW.id,NEW.classification,NEW.use_case,NEW.origin_sample) IS DISTINCT FROM (OLD.id,OLD.classification,OLD.use_case,OLD.origin_sample) THEN
 RAISE EXCEPTION 'Policy identity and samples are immutable' USING ERRCODE='23514'; END IF;
 RETURN NEW;
END; $$;
DROP TRIGGER IF EXISTS lifecycle_identity ON logai_policies;
CREATE TRIGGER lifecycle_identity BEFORE UPDATE OR DELETE ON logai_policies FOR EACH ROW EXECUTE FUNCTION logai_policy_identity_guard();
CREATE OR REPLACE FUNCTION logai_sample_version_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF EXISTS(SELECT 1 FROM logai_policies WHERE id=NEW.policy_id AND classification='SAMPLE' AND EXISTS(SELECT 1 FROM logai_policy_versions WHERE policy_id=NEW.policy_id)) THEN
 RAISE EXCEPTION 'Samples are read-only' USING ERRCODE='23514'; END IF;
 RETURN NEW;
END; $$;
DROP TRIGGER IF EXISTS lifecycle_sample_version ON logai_policy_versions;
CREATE TRIGGER lifecycle_sample_version BEFORE INSERT ON logai_policy_versions FOR EACH ROW EXECUTE FUNCTION logai_sample_version_guard();
CREATE TABLE IF NOT EXISTS logai_global_snapshots (
 id uuid PRIMARY KEY, sequence bigserial UNIQUE NOT NULL, actor text NOT NULL, reason text NOT NULL,
 generator_version text NOT NULL, generator_fingerprint char(64) NOT NULL,
 restored_from uuid REFERENCES logai_global_snapshots(id), created_at timestamptz NOT NULL DEFAULT now(),
 request_key text UNIQUE NOT NULL, request_hash char(64) NOT NULL
);
CREATE TABLE IF NOT EXISTS logai_snapshot_members (
 snapshot_id uuid NOT NULL REFERENCES logai_global_snapshots(id), use_case text NOT NULL CHECK(use_case='chute_allocation'),
 policy_id text NOT NULL, revision bigint NOT NULL, fingerprint char(64) NOT NULL,
 PRIMARY KEY(snapshot_id,use_case), UNIQUE(snapshot_id,policy_id),
 FOREIGN KEY(policy_id,revision) REFERENCES logai_policy_versions(policy_id,revision)
);
CREATE TABLE IF NOT EXISTS logai_current_snapshot (
 singleton boolean PRIMARY KEY DEFAULT true CHECK(singleton), snapshot_id uuid NOT NULL REFERENCES logai_global_snapshots(id)
);
CREATE TABLE IF NOT EXISTS logai_selection_reviews (
 id uuid PRIMARY KEY, policy_id text NOT NULL, revision bigint NOT NULL, fingerprint char(64) NOT NULL,
 reviewer text NOT NULL, consumed_snapshot uuid REFERENCES logai_global_snapshots(id), generator_fingerprint char(64) NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
 FOREIGN KEY(policy_id,revision) REFERENCES logai_policy_versions(policy_id,revision)
);
ALTER TABLE logai_selection_reviews ADD COLUMN IF NOT EXISTS consumed_snapshot uuid REFERENCES logai_global_snapshots(id);
CREATE OR REPLACE FUNCTION logai_snapshot_member_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF NOT EXISTS(SELECT 1 FROM logai_policies p JOIN logai_policy_versions v ON v.policy_id=p.id
 WHERE p.id=NEW.policy_id AND v.revision=NEW.revision AND p.classification='CUSTOMER'
 AND p.use_case=NEW.use_case AND v.customer_reviewed AND v.validation->>'valid'='true' AND v.checksum=NEW.fingerprint) THEN
 RAISE EXCEPTION 'Snapshot member must be an eligible customer revision' USING ERRCODE='23514'; END IF;
 IF NOT EXISTS(SELECT 1 FROM logai_global_snapshots WHERE id=NEW.snapshot_id AND xmin::text::bigint = txid_current() % 4294967296) THEN
 RAISE EXCEPTION 'Selected snapshot membership is immutable' USING ERRCODE='23514'; END IF;
 RETURN NEW;
END; $$;
DROP TRIGGER IF EXISTS lifecycle_member_guard ON logai_snapshot_members;
CREATE TRIGGER lifecycle_member_guard BEFORE INSERT ON logai_snapshot_members FOR EACH ROW EXECUTE FUNCTION logai_snapshot_member_guard();
CREATE OR REPLACE FUNCTION logai_current_snapshot_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF NOT EXISTS(SELECT 1 FROM logai_snapshot_members WHERE snapshot_id=NEW.snapshot_id AND use_case='chute_allocation') THEN
 RAISE EXCEPTION 'Global snapshot is incomplete' USING ERRCODE='23514'; END IF;
 RETURN NEW;
END; $$;
DROP TRIGGER IF EXISTS lifecycle_current_guard ON logai_current_snapshot;
CREATE TRIGGER lifecycle_current_guard BEFORE INSERT OR UPDATE ON logai_current_snapshot FOR EACH ROW EXECUTE FUNCTION logai_current_snapshot_guard();
DROP TRIGGER IF EXISTS lifecycle_snapshot_immutable ON logai_global_snapshots;
CREATE TRIGGER lifecycle_snapshot_immutable BEFORE UPDATE OR DELETE ON logai_global_snapshots FOR EACH ROW EXECUTE FUNCTION logai_policy_immutable();
DROP TRIGGER IF EXISTS lifecycle_member_immutable ON logai_snapshot_members;
CREATE TRIGGER lifecycle_member_immutable BEFORE UPDATE OR DELETE ON logai_snapshot_members FOR EACH ROW EXECUTE FUNCTION logai_policy_immutable();
DROP TRIGGER IF EXISTS lifecycle_review_immutable ON logai_selection_reviews;
CREATE OR REPLACE FUNCTION logai_selection_review_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF TG_OP='DELETE' OR (to_jsonb(NEW)-'consumed_snapshot') IS DISTINCT FROM (to_jsonb(OLD)-'consumed_snapshot')
 OR OLD.consumed_snapshot IS NOT NULL OR NEW.consumed_snapshot IS NULL THEN
 RAISE EXCEPTION 'Selection review is immutable and single use' USING ERRCODE='23514'; END IF;
 RETURN NEW;
END; $$;
CREATE TRIGGER lifecycle_review_immutable BEFORE UPDATE OR DELETE ON logai_selection_reviews FOR EACH ROW EXECUTE FUNCTION logai_selection_review_guard();
CREATE INDEX IF NOT EXISTS lifecycle_revision_snapshots ON logai_snapshot_members(policy_id,revision);

-- Dictionary values live in dedicated revisioned relational rows, not TypeScript.
CREATE TABLE IF NOT EXISTS logai_policy_definition_versions (
 policy_id text NOT NULL, revision bigint NOT NULL, stable_key text NOT NULL,
 position integer NOT NULL CHECK(position>=0),
 name text NOT NULL CHECK(length(trim(name)) BETWEEN 1 AND 120),
 description text NOT NULL CHECK(length(trim(description)) BETWEEN 1 AND 2000),
 kind text NOT NULL CHECK(kind IN ('noun','predicate','verb','keyword')),
 PRIMARY KEY(policy_id,revision,stable_key), UNIQUE(policy_id,revision,position),
 FOREIGN KEY(policy_id,revision) REFERENCES logai_policy_versions(policy_id,revision),
 FOREIGN KEY(policy_id,stable_key) REFERENCES logai_policy_definitions(policy_id,stable_key)
);
DROP TRIGGER IF EXISTS lifecycle_dictionary_immutable ON logai_policy_definition_versions;
CREATE TRIGGER lifecycle_dictionary_immutable BEFORE UPDATE OR DELETE ON logai_policy_definition_versions FOR EACH ROW EXECUTE FUNCTION logai_policy_immutable();
CREATE OR REPLACE FUNCTION logai_dictionary_insert_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF NOT EXISTS(SELECT 1 FROM logai_policy_versions WHERE policy_id=NEW.policy_id AND revision=NEW.revision
 AND xmin::text::bigint = txid_current() % 4294967296) THEN
 RAISE EXCEPTION 'Dictionary must be saved atomically with a new immutable revision' USING ERRCODE='23514'; END IF;
 RETURN NEW;
END; $$;
DROP TRIGGER IF EXISTS lifecycle_dictionary_insert ON logai_policy_definition_versions;
CREATE TRIGGER lifecycle_dictionary_insert BEFORE INSERT ON logai_policy_definition_versions FOR EACH ROW EXECUTE FUNCTION logai_dictionary_insert_guard();

CREATE OR REPLACE FUNCTION logai_complete_snapshot_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF NOT EXISTS(SELECT 1 FROM logai_snapshot_members WHERE snapshot_id=NEW.id AND use_case='chute_allocation') THEN
 RAISE EXCEPTION 'Every global snapshot must be complete' USING ERRCODE='23514'; END IF;
 RETURN NEW;
END; $$;
DROP TRIGGER IF EXISTS lifecycle_complete_snapshot ON logai_global_snapshots;
CREATE CONSTRAINT TRIGGER lifecycle_complete_snapshot AFTER INSERT ON logai_global_snapshots DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION logai_complete_snapshot_guard();
