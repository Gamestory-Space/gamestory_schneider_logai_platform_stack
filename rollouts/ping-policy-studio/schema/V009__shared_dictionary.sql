-- Shared customer dictionary. Existing per-policy manifests remain immutable evidence.
CREATE TABLE IF NOT EXISTS logai_shared_dictionary_versions (
 version bigint PRIMARY KEY CHECK(version>0), author text NOT NULL,
 request_key text NOT NULL UNIQUE, request_hash char(64) NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS logai_shared_dictionary_terms (
 dictionary_version bigint NOT NULL REFERENCES logai_shared_dictionary_versions(version),
 term_id text NOT NULL, definition_version bigint NOT NULL CHECK(definition_version>0),
 name text NOT NULL, description text NOT NULL,
 kind text NOT NULL CHECK(kind IN ('noun','predicate','verb','keyword')),
 position integer NOT NULL CHECK(position>=0),
 PRIMARY KEY(dictionary_version,term_id), UNIQUE(dictionary_version,position)
);
CREATE UNIQUE INDEX IF NOT EXISTS shared_dictionary_unique_names
 ON logai_shared_dictionary_terms(dictionary_version,lower(btrim(name)));
DO $$ DECLARE t text; BEGIN
 FOREACH t IN ARRAY ARRAY['logai_shared_dictionary_versions','logai_shared_dictionary_terms'] LOOP
 EXECUTE format('DROP TRIGGER IF EXISTS shared_dictionary_immutable ON %I',t);
 EXECUTE format('CREATE TRIGGER shared_dictionary_immutable BEFORE UPDATE OR DELETE ON %I FOR EACH ROW EXECUTE FUNCTION logai_policy_immutable()',t);
 END LOOP;
END $$;
CREATE OR REPLACE FUNCTION logai_shared_dictionary_insert_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF NOT EXISTS(SELECT 1 FROM logai_shared_dictionary_versions WHERE version=NEW.dictionary_version
 AND xmin::text::bigint=txid_current()%4294967296) THEN
 RAISE EXCEPTION 'Dictionary membership is immutable after creation' USING ERRCODE='23514'; END IF;
 RETURN NEW;
END; $$;
DROP TRIGGER IF EXISTS shared_dictionary_manifest_insert ON logai_shared_dictionary_terms;
CREATE TRIGGER shared_dictionary_manifest_insert BEFORE INSERT ON logai_shared_dictionary_terms FOR EACH ROW EXECUTE FUNCTION logai_shared_dictionary_insert_guard();
ALTER TABLE logai_policy_versions ADD COLUMN IF NOT EXISTS shared_dictionary_version bigint REFERENCES logai_shared_dictionary_versions(version);
