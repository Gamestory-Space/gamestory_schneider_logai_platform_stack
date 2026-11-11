# Local database credential recovery evidence

Validated 2026-10-29. API source commit:
`49a2c0d` in [API PR #2](https://github.com/Gamestory-Space/gamestory-logai-api/pull/2).
The platform changes and this evidence are submitted together for independent
review. No Schneider deployment or independent-validator acceptance is claimed.

## API validation

`api-tests.txt` and `database-recovery-results.xml` record **63 passing tests**,
including nine real PostgreSQL acceptance tests. No integration tests were skipped.
Used a disposable PostgreSQL 16.15 container, dummy local administrator credentials,
temporary per-test database logins/passwords, and the current source mounted into
the existing API runtime image with the new dependencies installed. Runtime:
Python 3.12, psycopg 3.2.3, SQLAlchemy 2.0.55, prometheus-client 0.21.1,
pytest 8.3.5. The existing API authentication regression tests were included.

The API PR's [PostgreSQL CI job](https://github.com/Gamestory-Space/gamestory-logai-api/actions/runs/40968289440/job/123778275020)
also passed (32 seconds). Text-log trailing whitespace is normalized for storage;
the JUnit XML is retained as generated.

The integration tests establish:

- Normal dictionary-row reads, writes, and implicit context commit work.
- A transaction inserts a row, retains the same backend PID across password
  rotation and pool replacement, continues writing, and commits all its work.
  A concurrent acquisition refreshes and writes successfully before the old
  transaction commits. Only the new generation remains after draining.
- Eight simultaneous real stale-password connection failures publish exactly
  one replacement generation; all eight writes complete and no connections
  remain checked out.
- A stale Secret returns a controlled failure, preserves the healthy transaction,
  then recovers after the file changes and backoff expires.
- A wrong replacement password never publishes its candidate; the old transaction
  still commits and later recovery succeeds.
- Transaction errors roll back without replay; even an in-transaction `28P01`
  does not enter connection-acquisition recovery.
- An actual API endpoint returns sanitized 503 during delayed Secret propagation,
  then succeeds after the mounted file changes. Metrics contain no test passwords.
- The real orchestration endpoint performs one SynQ call and persists its run
  using actual psycopg Jsonb values after connection recovery.

Recovery happens inside the same test process and manager; no restart mechanism
is invoked. Unit tests additionally cover atomic Secret symlink replacement,
missing/empty/unreadable values, bounded refresh-lock waits, concurrent
publication/reservations, draining shutdown, generation limits, password-free
logs, restricted authentication classification, and unchanged host/SSL settings.

## Helm validation

Helm v3.16.4 validation passed:

- `helm-recovery-tests.txt`: disabled/enabled rendering in all six environments,
  password-key/Secret overrides, directory mount without subPath, fsGroup 10001
  readability, and preserved non-API workloads, probes, and security settings.
- `helm-identity-tests.txt`: existing six-environment identity and service-account
  regression checks.
- `helm-lint-uat.txt`: UAT values plus the new recovery overlay lint successfully.
- `uat-api-deployment.yaml`: actual reference-chart API Deployment render with
  synthetic placeholder UAT settings. Its existing pinned image does not contain
  recovery; selecting a newly built release image remains a deployment gate.

Reproduce from the platform root:

```sh
python3 scripts/test-database-credential-recovery.py --helm /path/to/helm
python3 scripts/test-helm-identity.py --helm /path/to/helm
helm lint helm/gamestory-schneider-platform \
  -f environments/uat/values.yaml \
  -f environments/uat/database-credential-recovery.yaml
```

The actual Schneider chart is not available locally, so its render/deployment,
ESO synchronization, real rotation timing, new release-image gates, and
independent review remain outstanding external acceptance steps. Tests use local
TCP PostgreSQL authentication; preservation of `sslmode=require` is verified at
the creator-parameter boundary, not against Schneider RDS TLS.
