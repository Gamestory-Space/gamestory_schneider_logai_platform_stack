#!/usr/bin/env python3
"""Rehearse the client psql plan against an explicitly isolated PostgreSQL database."""
import hashlib
import json
import os
import re
from pathlib import Path
import shlex
import shutil
import tempfile
import subprocess
import unittest
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
PLAN = os.getenv('POLICY_ROLLOUT_TEST_DIR', str(ROOT / 'rollouts/ping-policy-studio'))
PSQL = shlex.split(os.environ['POLICY_ROLLOUT_TEST_PSQL'])
DB = 'policy_rollout_test'


def query(sql):
    result = subprocess.run([*PSQL, '-X', '-v', 'ON_ERROR_STOP=1', '-At', '-c', sql], capture_output=True, text=True)
    if result.returncode:
        raise AssertionError(result.stderr)
    return result.stdout.strip()


class MigrationRehearsal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if query('SELECT current_database()') != DB:
            raise RuntimeError('Tests require a separate policy_rollout_test database; refusing other targets.')

    def setUp(self):
        self.schema = 'rollout_test_' + uuid4().hex
        self.schemas = [self.schema]
        self.roles = []
        self.legacy_version = None
        query(f'CREATE SCHEMA {self.schema}')

    def tearDown(self):
        for schema in self.schemas:
            query(f'DROP SCHEMA {schema} CASCADE')
        for role in self.roles:
            query(f'DROP ROLE {role}')

    def plan(self, name=None, backup=True, as_role=None, **variables):
        args = {'expected_database': DB, 'target_schema': self.schema, **variables}
        if backup:
            args['backup_reference'] = 'isolated-test-backup'
        command = [*PSQL, '-X', '-v', 'ON_ERROR_STOP=1']
        for key, value in args.items():
            command += ['-v', f'{key}={value}']
        if as_role:
            command += ['-c',f'SET ROLE {as_role}; SET search_path TO {self.schema},pg_catalog']
        if name:
            return subprocess.run([*command, '-f', PLAN + '/' + name], capture_output=True, text=True)
        if not backup or args['expected_database'] != DB or args['target_schema'] != self.schema:
            return subprocess.CompletedProcess(command, 1, '', 'Invalid fixture target or backup')
        history = query(f"SELECT to_regclass('{self.schema}.logai_flyway_schema_history') IS NOT NULL")
        if history == 'f' and self.legacy_version:
            inventory = self.plan('preflight.psql', backup=False)
            if inventory.returncode:
                return inventory
            baseline = self.flyway('baseline', f'-baselineVersion={self.legacy_version}')
            if baseline.returncode:
                return baseline
        return self.flyway('migrate')

    def flyway(self, *args, migrations=None):
        command = [
            'docker', 'run', '--rm', '--network', 'host',
            '-v', f'{migrations or Path(PLAN).resolve() / "schema"}:/flyway/sql:ro',
            '-e', f"FLYWAY_URL=jdbc:postgresql://{os.environ['PGHOST']}:{os.environ['PGPORT']}/{DB}",
            '-e', f"FLYWAY_USER={os.environ['PGUSER']}",
            '-e', 'FLYWAY_PASSWORD',
            'docker.io/redgate/flyway:11.20.0',
            f'-schemas={self.schema}', '-table=logai_flyway_schema_history',
            '-createSchemas=false', '-baselineOnMigrate=false', '-group=true', *args,
        ]
        return subprocess.run(command, env={**os.environ, 'FLYWAY_PASSWORD': os.environ['PGPASSWORD']},
                              capture_output=True, text=True)

    def file(self, name):
        name = re.sub(r'^(\d+)_', r'V\1__', name)
        return subprocess.run([*PSQL, '-X', '-v', 'ON_ERROR_STOP=1', '-c', f'SET search_path TO {self.schema},pg_catalog', '-f', PLAN + '/schema/' + name], capture_output=True, text=True)

    def fingerprint(self, table, columns):
        select = ','.join('"'+column+'"' for column in columns)
        return query(f"SELECT md5(coalesce(string_agg(to_jsonb(t)::text,E'\\n' ORDER BY to_jsonb(t)::text),'')) FROM (SELECT {select} FROM {self.schema}.{table}) t")

    def existing_data(self, policies=False, backend="postgres"):
        for name in ['001_release_and_chutes_read_models.sql','003_order_orchestration_runs.sql']:
            result = self.file(name)
            self.assertEqual(result.returncode, 0, result.stderr)
        query(f"""SET search_path TO {self.schema},pg_catalog;
          CREATE TABLE unrelated_existing(id integer PRIMARY KEY,value text NOT NULL);
          INSERT INTO unrelated_existing VALUES(1,'retain unrelated client data');
          INSERT INTO logai_release_shipments(id,tenant_id,site_id,business_date,shipment_id,status,mode)
          VALUES('00000000-0000-4000-8000-000000000001','test-tenant','test-site','2026-11-17','existing-shipment','paused','manual');
          INSERT INTO logai_chutes(id,tenant_id,site_id,business_date,chute_number)
          VALUES('00000000-0000-4000-8000-000000000002','test-tenant','test-site','2026-11-17',7);
          INSERT INTO logai_order_orchestration_runs(id,tenant_id,site_id,business_date,ai_mode,status)
          VALUES('00000000-0000-4000-8000-000000000003','test-tenant','test-site','2026-11-17','suggest','existing');
        """)
        self.legacy_version = 3
        if policies:
            self.legacy_version = 4
            result = self.file('004_policy_persistence.sql')
            self.assertEqual(result.returncode, 0, result.stderr)
            location = hashlib.sha256(json.dumps([backend]).encode()).hexdigest()
            body = 'id: legacy-policy\nname: Legacy policy\ndefinitions:\n  - key: retained_term\n    name: Retained term\n    description: Retained legacy meaning\n    kind: noun\nconfiguration: null\nrules: []\nobjectives: []\ncategories: []\n'
            checksum = hashlib.sha256(body.encode()).hexdigest()
            query(f"""SET search_path TO {self.schema},pg_catalog;
             INSERT INTO logai_policy_storage VALUES(true,'{backend}','{location}');
             INSERT INTO logai_policies(id,head_revision,created_by) VALUES('legacy-policy',1,'previous-author');
             INSERT INTO logai_policy_versions(policy_id,revision,name,status,backend,yaml_text,checksum,author,validation)
             VALUES('legacy-policy',1,'Legacy policy','draft','postgres',$body${body}$body$,'{checksum}','previous-author','{{"valid":false,"issues":[]}}');
             INSERT INTO logai_policy_definitions VALUES('legacy-policy','retained_term',1);
            """)
        # Isolated fixture construction only; the shipped plan never disables history guards.
        if policies and backend == 's3':
            query(f"""SET search_path TO {self.schema},pg_catalog;
             DROP TRIGGER policy_snapshot_immutable ON logai_policy_versions;
             UPDATE logai_policy_versions SET backend='s3',yaml_text=NULL,object_key='legacy-policy/object.yaml',object_version_id='retained-version-1';
             CREATE TRIGGER policy_snapshot_immutable BEFORE UPDATE OR DELETE ON logai_policy_versions FOR EACH ROW EXECUTE FUNCTION logai_policy_immutable();
            """)
        return self.existing_fingerprints()

    def existing_fingerprints(self):
        tables = query(f"SELECT table_name FROM information_schema.tables WHERE table_schema='{self.schema}' ORDER BY table_name").splitlines()
        result = {}
        for table in tables:
            columns = query(f"SELECT column_name FROM information_schema.columns WHERE table_schema='{self.schema}' AND table_name='{table}' ORDER BY ordinal_position").splitlines()
            result[table] = (columns, self.fingerprint(table, columns))
        return result

    def assert_preserved(self, baseline):
        for table, (columns, fingerprint) in baseline.items():
            self.assertEqual(self.fingerprint(table, columns), fingerprint, table)

    def test_populated_core_tables_preserved_and_no_customer_seed(self):
        baseline = self.existing_data()
        inventory = self.plan('preflight.psql', backup=False)
        self.assertEqual(inventory.returncode, 0, inventory.stderr)
        result = self.plan()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_preserved(baseline)
        self.assertEqual(query(f'SELECT count(*) FROM {self.schema}.logai_policies'), '0')
        self.assertEqual(query(f'SELECT count(*) FROM {self.schema}.logai_global_snapshots'), '0')
        self.assertEqual(query(f'SELECT count(*) FROM {self.schema}.logai_shared_dictionary_versions'), '0')
        self.assertEqual(self.plan().returncode, 0)
        self.assert_preserved(baseline)

    def test_checksum_drift_and_failed_migration_recovery(self):
        result = self.plan()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        with tempfile.TemporaryDirectory() as directory:
            migrations = Path(directory) / 'schema'
            shutil.copytree(Path(PLAN) / 'schema', migrations)
            original = migrations / 'V001__release_and_chutes_read_models.sql'
            original.write_text(original.read_text() + '\nSELECT 1;\n')
            drift = self.flyway('validate', migrations=migrations)
            self.assertNotEqual(drift.returncode, 0)
            self.assertIn('checksum mismatch', (drift.stdout + drift.stderr).lower())
            shutil.copyfile(Path(PLAN) / 'schema' / original.name, original)

            candidate = migrations / 'V012__recovery_fixture.sql'
            candidate.write_text('CREATE TABLE recovery_fixture(id int); SELECT 1/0;')
            failed = self.flyway('migrate', migrations=migrations)
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn('division by zero', failed.stdout + failed.stderr)
            self.assertEqual(query(f"SELECT to_regclass('{self.schema}.recovery_fixture') IS NULL"), 't')
            candidate.write_text('CREATE TABLE recovery_fixture(id int);')
            recovered = self.flyway('migrate', migrations=migrations)
            self.assertEqual(recovered.returncode, 0, recovered.stdout + recovered.stderr)

    def test_liquibase_objects_preserved_during_legacy_adoption(self):
        self.existing_data()
        query(f"""CREATE TABLE {self.schema}.databasechangelog(id text primary key);
            INSERT INTO {self.schema}.databasechangelog VALUES ('keycloak-fixture');
            CREATE TABLE {self.schema}.databasechangeloglock(id int primary key, locked boolean);
            INSERT INTO {self.schema}.databasechangeloglock VALUES (1, false);
            CREATE TABLE {self.schema}.realm(id text primary key);
            INSERT INTO {self.schema}.realm VALUES ('test-realm');
            CREATE TABLE {self.schema}.user_entity(id text primary key);
            INSERT INTO {self.schema}.user_entity VALUES ('test-user')""")
        baseline = self.existing_fingerprints()
        result = self.plan()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assert_preserved(baseline)

    def test_existing_policy_history_and_backend_registry_preserved(self):
        baseline = self.existing_data(policies=True)
        result = self.plan()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_preserved(baseline)
        self.assertEqual(query(f'SELECT count(*) FROM {self.schema}.logai_policies'), '1')
        self.assertEqual(self.plan().returncode, 0)
        self.assert_preserved(baseline)

    def test_existing_s3_metadata_preserved_without_accessing_objects(self):
        baseline = self.existing_data(policies=True,backend='s3')
        result = self.plan()
        self.assertEqual(result.returncode,0,result.stderr)
        self.assert_preserved(baseline)
        self.assertEqual(self.plan().returncode,0)
        self.assert_preserved(baseline)

    def test_repeat_plan_preserves_new_normalized_task_and_intelligence_choice(self):
        self.assertEqual(self.plan().returncode,0)
        document={'id':'order-release','name':'Order Release','definitions':[], 'configuration':None,'configurationTerms':{},'settings':[], 'rules':[],'objectives':[],'categories':[],
          'useCase':{'intelligenceOption':'enterprise_ai','task':'Release eligible shipments.','purpose':'','decisionRequired':'','inputs':'Shipment details.','expectedResult':'Release result.'}}
        checksum=hashlib.sha256(json.dumps(document,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        location=hashlib.sha256(json.dumps(['postgres']).encode()).hexdigest()
        query(f"""SET search_path TO {self.schema},pg_catalog;
         INSERT INTO logai_policy_storage VALUES(true,'postgres','{location}');
         INSERT INTO logai_policies(id,head_revision,created_by,use_case) VALUES('order-release',1,'test-author','order_release');
         INSERT INTO logai_policy_versions(policy_id,revision,name,status,backend,checksum,author,validation,content_schema)
         VALUES('order-release',1,'Order Release','draft','relational','{checksum}','test-author','{{"valid":false,"issues":[]}}',4);
         INSERT INTO logai_policy_use_case_details(policy_id,revision,purpose,decision_required,inputs,expected_result,task,intelligence_option)
         VALUES('order-release',1,'','','Shipment details.','Release result.','Release eligible shipments.','enterprise_ai');
        """)
        columns=['policy_id','revision','purpose','decision_required','inputs','expected_result','task','intelligence_option']
        before=self.fingerprint('logai_policy_use_case_details',columns)
        result=self.plan();self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(self.fingerprint('logai_policy_use_case_details',columns),before)

    def test_incompatible_existing_table_rejected_before_any_schema_change(self):
        query(f'CREATE TABLE {self.schema}.logai_policies(id integer PRIMARY KEY)')
        result = self.plan()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('non-empty', result.stdout + result.stderr)
        self.assertEqual(query(f"SELECT count(*) FROM information_schema.tables WHERE table_schema='{self.schema}'"), '1')

    def test_later_constraint_failure_rolls_back_earlier_ddl(self):
        baseline = self.existing_data(policies=True)
        query(f"""SET search_path TO {self.schema},pg_catalog;
          ALTER TABLE logai_policy_versions DROP CONSTRAINT logai_policy_versions_backend_check;
          ALTER TABLE logai_policy_versions DROP CONSTRAINT logai_policy_versions_check;
          DROP TRIGGER policy_snapshot_immutable ON logai_policy_versions;
          UPDATE logai_policy_versions SET backend='client-custom-backend';
        """)
        columns = baseline['logai_policy_versions'][0]
        before = self.fingerprint('logai_policy_versions', columns)
        result = self.plan()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.fingerprint('logai_policy_versions', columns), before)
        self.assertEqual(query(f"SELECT count(*) FROM information_schema.columns WHERE table_schema='{self.schema}' AND table_name='logai_policies' AND column_name='classification'"), '0')
        self.assertEqual(query(f"SELECT to_regclass('{self.schema}.logai_global_snapshots') IS NULL"), 't')

    def test_missing_backup_wrong_database_and_wrong_schema_rejected(self):
        self.assertNotEqual(self.plan(backup=False).returncode, 0)
        self.assertNotEqual(self.plan(expected_database='not-the-target').returncode, 0)
        self.assertNotEqual(self.plan(target_schema='missing_' + uuid4().hex).returncode, 0)
        self.assertEqual(query(f"SELECT count(*) FROM information_schema.tables WHERE table_schema='{self.schema}'"), '0')

    def test_policy_rows_without_registered_backend_rejected(self):
        self.existing_data(policies=True)
        query(f'DELETE FROM {self.schema}.logai_policy_storage')
        result = self.plan()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('registered backend', result.stderr)
        self.assertEqual(query(f"SELECT to_regclass('{self.schema}.logai_global_snapshots') IS NULL"), 't')

    def test_conflicting_reserved_policy_identity_rejected(self):
        self.existing_data(policies=True)
        query(f"INSERT INTO {self.schema}.logai_policies(id,head_revision,created_by) VALUES('order-release',0,'legacy-author')")
        result=self.plan();self.assertNotEqual(result.returncode,0)
        self.assertIn('use-case reconciliation',result.stderr)
        self.assertEqual(query(f"SELECT count(*) FROM {self.schema}.logai_policies"),'2')
        self.assertEqual(query(f"SELECT to_regclass('{self.schema}.logai_global_snapshots') IS NULL"),'t')

    def test_keycloak_schema_rejected(self):
        query(f'CREATE TABLE {self.schema}.user_entity(id text); CREATE TABLE {self.schema}.realm(id text)')
        result = self.plan()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('non-empty',result.stdout + result.stderr)
        self.assertEqual(query(f"SELECT count(*) FROM information_schema.tables WHERE table_schema='{self.schema}'"),'2')

    def test_target_schema_collision_detected(self):
        other = 'rollout_test_' + uuid4().hex
        self.schemas.append(other)
        query(f'CREATE SCHEMA {other}; CREATE TABLE {other}.logai_chutes(id uuid)')
        result = self.plan('preflight.psql', backup=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('another schema', result.stderr)

    def test_runtime_grants_do_not_allow_history_updates_or_ddl(self):
        result = self.plan()
        self.assertEqual(result.returncode, 0, result.stderr)
        role = 'rollout_role_' + uuid4().hex
        self.roles.append(role)
        query(f'CREATE ROLE {role}')
        result = self.plan('grant-runtime.psql', backup=False, runtime_role=role)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(query(f"SELECT has_table_privilege('{role}','{self.schema}.logai_policy_versions','SELECT') AND has_table_privilege('{role}','{self.schema}.logai_policy_versions','INSERT')"), 't')
        self.assertEqual(query(f"SELECT has_table_privilege('{role}','{self.schema}.logai_policy_versions','UPDATE,DELETE,TRUNCATE')"), 'f')
        self.assertEqual(query(f"SELECT has_column_privilege('{role}','{self.schema}.logai_policies','head_revision','UPDATE')"), 't')
        query(f"""SET ROLE {role}; SET search_path TO {self.schema},pg_catalog;
          BEGIN;
          INSERT INTO logai_policy_storage VALUES(true,'postgres','{'0'*64}') ON CONFLICT(singleton) DO UPDATE SET backend=excluded.backend,location_hash=excluded.location_hash;
          INSERT INTO logai_shared_dictionary_versions(version,author,request_key,request_hash) VALUES(1,'test-author','grant-test-key','{'0'*64}');
          INSERT INTO logai_shared_dictionary_terms(dictionary_version,term_id,definition_version,name,description,kind,position) VALUES(1,'grant_test_term',1,'Test term','Test meaning','noun',0);
          SELECT nextval('logai_policy_audit_id_seq');
          SELECT nextval('logai_global_snapshots_sequence_seq');
          COMMIT;
        """)
        for table in ['logai_release_shipments','logai_chutes','logai_order_orchestration_runs']:
            query(f'GRANT SELECT ON {self.schema}.{table} TO {role}')
        self.assertEqual(self.plan('runtime-check.psql',backup=False,as_role=role).returncode,0)
        query(f'REVOKE INSERT ON {self.schema}.logai_shared_dictionary_terms FROM {role}')
        self.assertNotEqual(self.plan('runtime-check.psql',backup=False,as_role=role).returncode,0)
        self.assertEqual(query(f"SELECT has_schema_privilege('{role}','{self.schema}','CREATE')"), 'f')


if __name__ == '__main__':
    unittest.main()
