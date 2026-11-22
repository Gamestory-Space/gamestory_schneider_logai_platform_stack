-- Independent definition revisions and dictionary manifests. No legacy rows rewritten.
CREATE TABLE IF NOT EXISTS logai_definition_revisions (
 policy_id text NOT NULL, stable_key text NOT NULL, version bigint NOT NULL CHECK(version>0),
 name text NOT NULL, description text NOT NULL, kind text NOT NULL CHECK(kind IN ('noun','predicate','verb','keyword')),
 fingerprint char(64) NOT NULL, author text NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(policy_id,stable_key,version),
 FOREIGN KEY(policy_id,stable_key) REFERENCES logai_policy_definitions(policy_id,stable_key)
);
CREATE TABLE IF NOT EXISTS logai_dictionary_versions (
 policy_id text NOT NULL REFERENCES logai_policies(id), version bigint NOT NULL CHECK(version>0),
 fingerprint char(64) NOT NULL, author text NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(policy_id,version), UNIQUE(policy_id,fingerprint)
);
CREATE TABLE IF NOT EXISTS logai_dictionary_members (
 policy_id text NOT NULL, dictionary_version bigint NOT NULL, stable_key text NOT NULL,
 definition_version bigint NOT NULL, position integer NOT NULL CHECK(position>=0),
 PRIMARY KEY(policy_id,dictionary_version,stable_key), UNIQUE(policy_id,dictionary_version,position),
 FOREIGN KEY(policy_id,dictionary_version) REFERENCES logai_dictionary_versions(policy_id,version),
 FOREIGN KEY(policy_id,stable_key,definition_version) REFERENCES logai_definition_revisions(policy_id,stable_key,version)
);
ALTER TABLE logai_policy_versions ADD COLUMN IF NOT EXISTS dictionary_version bigint;
DO $$ BEGIN
 IF NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conname='policy_dictionary_version' AND conrelid='logai_policy_versions'::regclass) THEN
 ALTER TABLE logai_policy_versions ADD CONSTRAINT policy_dictionary_version FOREIGN KEY(policy_id,dictionary_version) REFERENCES logai_dictionary_versions(policy_id,version);
 END IF;
END $$;
DO $$ DECLARE t text; BEGIN
 FOREACH t IN ARRAY ARRAY['logai_definition_revisions','logai_dictionary_versions','logai_dictionary_members'] LOOP
 EXECUTE format('DROP TRIGGER IF EXISTS dictionary_history_immutable ON %I',t);
 EXECUTE format('CREATE TRIGGER dictionary_history_immutable BEFORE UPDATE OR DELETE ON %I FOR EACH ROW EXECUTE FUNCTION logai_policy_immutable()',t);
 END LOOP;
END $$;
CREATE OR REPLACE FUNCTION logai_dictionary_member_insert_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF NOT EXISTS(SELECT 1 FROM logai_dictionary_versions WHERE policy_id=NEW.policy_id AND version=NEW.dictionary_version
 AND xmin::text::bigint=txid_current()%4294967296) THEN
 RAISE EXCEPTION 'Dictionary membership is immutable after creation' USING ERRCODE='23514'; END IF;
 RETURN NEW;
END; $$;
DROP TRIGGER IF EXISTS dictionary_manifest_insert ON logai_dictionary_members;
CREATE TRIGGER dictionary_manifest_insert BEFORE INSERT ON logai_dictionary_members FOR EACH ROW EXECUTE FUNCTION logai_dictionary_member_insert_guard();
