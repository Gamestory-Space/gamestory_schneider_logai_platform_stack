-- New task briefs; existing purpose/decision columns and values remain immutable.
ALTER TABLE logai_policy_use_case_details ADD COLUMN IF NOT EXISTS task text CHECK(length(task)<=8002);
ALTER TABLE logai_policy_use_case_details ADD COLUMN IF NOT EXISTS intelligence_option text CHECK(intelligence_option IN ('self_hosted_ai','deterministic','enterprise_ai'));
ALTER TABLE logai_policy_versions DROP CONSTRAINT IF EXISTS logai_policy_versions_content_schema_check;
ALTER TABLE logai_policy_versions ADD CONSTRAINT logai_policy_versions_content_schema_check CHECK(content_schema IN (1,2,3,4));
CREATE OR REPLACE FUNCTION logai_policy_identity_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF TG_OP='UPDATE' AND OLD.classification='SAMPLE'
 AND current_setting('logai.sample_guide_upgrade',true)='four-sections-v1'
 AND (to_jsonb(NEW)-'head_revision')=(to_jsonb(OLD)-'head_revision')
 AND NEW.head_revision=OLD.head_revision+1
 AND NOT EXISTS(SELECT 1 FROM logai_policy_use_case_details WHERE policy_id=OLD.id AND revision=OLD.head_revision AND task IS NOT NULL) THEN RETURN NEW; END IF;
 IF TG_OP='DELETE' OR OLD.classification='SAMPLE' OR
 (NEW.id,NEW.classification,NEW.use_case,NEW.origin_sample) IS DISTINCT FROM (OLD.id,OLD.classification,OLD.use_case,OLD.origin_sample) THEN
 RAISE EXCEPTION 'Policy identity and samples are immutable' USING ERRCODE='23514'; END IF;
 RETURN NEW;
END; $$;
CREATE OR REPLACE FUNCTION logai_sample_version_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF EXISTS(SELECT 1 FROM logai_policies WHERE id=NEW.policy_id AND classification='SAMPLE'
 AND EXISTS(SELECT 1 FROM logai_policy_versions WHERE policy_id=NEW.policy_id)) THEN
 IF current_setting('logai.sample_guide_upgrade',true)='four-sections-v1' AND NEW.content_schema=4
 AND NEW.revision=(SELECT head_revision FROM logai_policies WHERE id=NEW.policy_id)
 AND NEW.revision=(SELECT max(revision)+1 FROM logai_policy_versions WHERE policy_id=NEW.policy_id)
 AND NOT EXISTS(SELECT 1 FROM logai_policy_use_case_details WHERE policy_id=NEW.policy_id AND task IS NOT NULL) THEN RETURN NEW; END IF;
 RAISE EXCEPTION 'Samples are read-only' USING ERRCODE='23514'; END IF;
 RETURN NEW;
END; $$;
