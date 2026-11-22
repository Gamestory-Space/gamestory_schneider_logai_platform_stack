-- Additive, repeatable migration. Publication remains disabled by application config.
CREATE TABLE IF NOT EXISTS logai_policy_storage (
 singleton boolean PRIMARY KEY DEFAULT true CHECK (singleton),
 backend text NOT NULL CHECK (backend IN ('postgres','s3')),
 location_hash char(64) NOT NULL
);
CREATE TABLE IF NOT EXISTS logai_policies (
 id text PRIMARY KEY, head_revision bigint NOT NULL DEFAULT 0,
 active_revision bigint, created_by text NOT NULL, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS logai_policy_versions (
 policy_id text NOT NULL REFERENCES logai_policies(id), revision bigint NOT NULL CHECK (revision>0),
 name text NOT NULL, status text NOT NULL CHECK (status IN ('draft','published')),
 backend text NOT NULL CHECK (backend IN ('postgres','s3')),
 yaml_text text, object_key text, object_version_id text,
 checksum char(64) NOT NULL, author text NOT NULL, validation jsonb NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now(), approval_id uuid,
 PRIMARY KEY(policy_id,revision),
 CHECK ((backend='postgres' AND yaml_text IS NOT NULL AND object_key IS NULL AND object_version_id IS NULL)
 OR (backend='s3' AND yaml_text IS NULL AND object_key IS NOT NULL AND object_version_id IS NOT NULL AND object_version_id<>'null'))
);
CREATE TABLE IF NOT EXISTS logai_policy_definitions (
 policy_id text NOT NULL REFERENCES logai_policies(id), stable_key text NOT NULL,
 first_revision bigint NOT NULL, PRIMARY KEY(policy_id,stable_key)
);
CREATE TABLE IF NOT EXISTS logai_policy_write_intents (
 policy_id text NOT NULL, request_key text NOT NULL, request_hash char(64) NOT NULL,
 object_key text, actor text NOT NULL,
 state text NOT NULL DEFAULT 'prepared' CHECK(state IN ('prepared','committed','abandoned')),
 result_revision bigint, created_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(policy_id,request_key)
);
CREATE TABLE IF NOT EXISTS logai_policy_approvals (
 id uuid PRIMARY KEY, policy_id text NOT NULL REFERENCES logai_policies(id),
 operation text NOT NULL CHECK(operation IN ('publish','rollback')),
 expected_revision bigint NOT NULL, source_revision bigint NOT NULL, checksum char(64) NOT NULL,
 approver text NOT NULL, request_key text NOT NULL, request_hash char(64) NOT NULL,
 consumed_revision bigint, created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(policy_id,request_key)
);
CREATE TABLE IF NOT EXISTS logai_policy_audit (
 id bigserial PRIMARY KEY, policy_id text NOT NULL, revision bigint,
 operation text NOT NULL, actor text NOT NULL, context jsonb NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now()
);
CREATE OR REPLACE FUNCTION logai_policy_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'Policy snapshots and audit records are immutable' USING ERRCODE='23514'; END;
$$;
DROP TRIGGER IF EXISTS policy_snapshot_immutable ON logai_policy_versions;
CREATE TRIGGER policy_snapshot_immutable BEFORE UPDATE OR DELETE ON logai_policy_versions FOR EACH ROW EXECUTE FUNCTION logai_policy_immutable();
DROP TRIGGER IF EXISTS policy_audit_immutable ON logai_policy_audit;
CREATE TRIGGER policy_audit_immutable BEFORE UPDATE OR DELETE ON logai_policy_audit FOR EACH ROW EXECUTE FUNCTION logai_policy_immutable();
DROP TRIGGER IF EXISTS policy_definition_identity_immutable ON logai_policy_definitions;
CREATE TRIGGER policy_definition_identity_immutable BEFORE UPDATE OR DELETE ON logai_policy_definitions FOR EACH ROW EXECUTE FUNCTION logai_policy_immutable();
CREATE INDEX IF NOT EXISTS policy_intents_reconcile ON logai_policy_write_intents(state,created_at);
CREATE INDEX IF NOT EXISTS policy_audit_history ON logai_policy_audit(policy_id,id);
CREATE OR REPLACE FUNCTION logai_policy_approval_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF TG_OP='DELETE' THEN RAISE EXCEPTION 'Approvals cannot be deleted' USING ERRCODE='23514'; END IF;
 IF (to_jsonb(NEW)-'consumed_revision') IS DISTINCT FROM (to_jsonb(OLD)-'consumed_revision')
 OR OLD.consumed_revision IS NOT NULL OR NEW.consumed_revision IS NULL THEN
 RAISE EXCEPTION 'Approval review is immutable and single-use' USING ERRCODE='23514'; END IF;
 RETURN NEW;
END;
$$;
DROP TRIGGER IF EXISTS policy_approval_immutable ON logai_policy_approvals;
CREATE TRIGGER policy_approval_immutable BEFORE UPDATE OR DELETE ON logai_policy_approvals FOR EACH ROW EXECUTE FUNCTION logai_policy_approval_guard();
