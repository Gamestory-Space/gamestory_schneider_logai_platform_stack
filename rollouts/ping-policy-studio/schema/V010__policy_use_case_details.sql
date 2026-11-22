-- Versioned task context. Historical policy revisions are not backfilled.
CREATE TABLE IF NOT EXISTS logai_policy_use_case_details (
 policy_id text NOT NULL, revision bigint NOT NULL,
 purpose text NOT NULL CHECK(length(purpose)<=4000),
 decision_required text NOT NULL CHECK(length(decision_required)<=4000),
 inputs text NOT NULL CHECK(length(inputs)<=4000),
 expected_result text NOT NULL CHECK(length(expected_result)<=4000),
 PRIMARY KEY(policy_id,revision),
 FOREIGN KEY(policy_id,revision) REFERENCES logai_policy_versions(policy_id,revision)
);
DROP TRIGGER IF EXISTS use_case_details_immutable ON logai_policy_use_case_details;
CREATE TRIGGER use_case_details_immutable BEFORE UPDATE OR DELETE ON logai_policy_use_case_details FOR EACH ROW EXECUTE FUNCTION logai_policy_immutable();
DROP TRIGGER IF EXISTS use_case_details_insert ON logai_policy_use_case_details;
CREATE TRIGGER use_case_details_insert BEFORE INSERT ON logai_policy_use_case_details FOR EACH ROW EXECUTE FUNCTION logai_dictionary_insert_guard();
ALTER TABLE logai_policy_versions DROP CONSTRAINT IF EXISTS logai_policy_versions_content_schema_check;
ALTER TABLE logai_policy_versions ADD CONSTRAINT logai_policy_versions_content_schema_check CHECK(content_schema IN (1,2,3,4));
-- Explicit administrator seed can append the context-bearing reference guide once.
-- Older sample revisions and their values stay immutable; ordinary sample writes fail.
CREATE OR REPLACE FUNCTION logai_policy_identity_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF TG_OP='UPDATE' AND OLD.classification='SAMPLE'
 AND current_setting('logai.sample_guide_upgrade',true)='use-case-v1'
 AND (to_jsonb(NEW)-'head_revision')=(to_jsonb(OLD)-'head_revision')
 AND NEW.head_revision=OLD.head_revision+1
 AND NOT EXISTS(SELECT 1 FROM logai_policy_use_case_details WHERE policy_id=OLD.id AND revision=OLD.head_revision) THEN
 RETURN NEW;
 END IF;
 IF TG_OP='DELETE' OR OLD.classification='SAMPLE' OR
 (NEW.id,NEW.classification,NEW.use_case,NEW.origin_sample) IS DISTINCT FROM (OLD.id,OLD.classification,OLD.use_case,OLD.origin_sample) THEN
 RAISE EXCEPTION 'Policy identity and samples are immutable' USING ERRCODE='23514'; END IF;
 RETURN NEW;
END; $$;
CREATE OR REPLACE FUNCTION logai_sample_version_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF EXISTS(SELECT 1 FROM logai_policies WHERE id=NEW.policy_id AND classification='SAMPLE'
 AND EXISTS(SELECT 1 FROM logai_policy_versions WHERE policy_id=NEW.policy_id)) THEN
 IF current_setting('logai.sample_guide_upgrade',true)='use-case-v1' AND NEW.content_schema=3
 AND NEW.revision=(SELECT head_revision FROM logai_policies WHERE id=NEW.policy_id)
 AND NEW.revision=(SELECT max(revision)+1 FROM logai_policy_versions WHERE policy_id=NEW.policy_id)
 AND NOT EXISTS(SELECT 1 FROM logai_policy_use_case_details WHERE policy_id=NEW.policy_id) THEN RETURN NEW; END IF;
 RAISE EXCEPTION 'Samples are read-only' USING ERRCODE='23514'; END IF;
 RETURN NEW;
END; $$;
