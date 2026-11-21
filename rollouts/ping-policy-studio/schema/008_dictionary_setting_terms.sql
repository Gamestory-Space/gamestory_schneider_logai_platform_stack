-- Existing rows remain historical/unbound; new setting rows must reference exact
-- definition values from the same immutable policy revision.
ALTER TABLE logai_policy_settings ADD COLUMN IF NOT EXISTS dictionary_key text;
DO $$ BEGIN
 IF NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conname='setting_dictionary_term' AND conrelid='logai_policy_settings'::regclass) THEN
 ALTER TABLE logai_policy_settings ADD CONSTRAINT setting_dictionary_term
 FOREIGN KEY(policy_id,revision,dictionary_key) REFERENCES logai_policy_definition_versions(policy_id,revision,stable_key)
 DEFERRABLE INITIALLY DEFERRED;
 END IF;
END $$;
CREATE OR REPLACE FUNCTION logai_setting_term_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF NEW.dictionary_key IS NULL THEN
 RAISE EXCEPTION 'New operating settings must select Dictionary entries' USING ERRCODE='23514'; END IF;
 RETURN NEW;
END; $$;
DROP TRIGGER IF EXISTS operating_setting_dictionary ON logai_policy_settings;
CREATE TRIGGER operating_setting_dictionary BEFORE INSERT ON logai_policy_settings FOR EACH ROW EXECUTE FUNCTION logai_setting_term_guard();

ALTER TABLE logai_policy_versions DROP CONSTRAINT IF EXISTS logai_policy_versions_content_schema_check;
ALTER TABLE logai_policy_versions ADD CONSTRAINT logai_policy_versions_content_schema_check CHECK(content_schema IN (1,2,3,4));
