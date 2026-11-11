# Dynamic database credential rotation: engineering assessment

Assessed 2026-10-29 against the local platform and API checkouts on
`release/v0.1.7`. Requirements source:
`handover/PRD LogAI API Dynamic Database Credential Rotation Recovery.md`.

## Current architecture

- The API is in the sibling `gamestory-logai-api` repository.
- `app/db.py:get_db()` opens a synchronous psycopg connection per context.
  There is no SQLAlchemy dependency, session factory, engine, or pool.
- All database-backed routes and schema initialization use this boundary.
  Routes use psycopg dictionary rows, `%s` parameters, explicit commits,
  and, in orchestration/callbacks, psycopg `Jsonb` wrappers.
- `app/config.py` caches settings, including `DATABASE_URL`; there is no
  mounted-password provider or recovery path.
- Orchestration performs external SynQ/Cognos/Teams operations before its
  database insert. Recovery must never replay the route or those operations.
- The reference Deployment lives in
  `helm/gamestory-schneider-platform/templates/apps.yaml`. It obtains
  `DATABASE_URL` from the selected existing database Secret. Retain UID/GID
  10001, the existing tmp mount, probes, and security settings.
- The Schneider chart named in the PRD is not present locally. The existing
  `handover/schneider-argocd` directory contains transfer fragments rather than
  that full chart. Reference-chart rendering cannot validate the absent chart.

## Authentication failure reproduced

Used a disposable local PostgreSQL 16 container, dummy credentials, and current
API source mounted into the released `logai-api-v0.1.7` image. The runtime
confirmed psycopg **3.2.3**, matching `requirements.txt`.

The control connection with the correct password executed `SELECT 1`
successfully. Calling the actual `get_db()` with a wrong password produced:

```text
psycopg.OperationalError: connection failed: connection to server at "127.0.0.1", port 55439 failed: FATAL:  password authentication failed for user "logai_probe"
```

Observed exception fields:

```json
{
  "sqlstate": null,
  "diag_sqlstate": null,
  "isinstance_InvalidPassword": false
}
```

An ASGI HTTP test using the actual app, development authentication disabled,
and startup schema/seeding disabled observed:

| Request | Status | Body |
| --- | --- | --- |
| `/api/v1/release` | 500 | `Internal Server Error` |
| `/health` | 200 | `{"status":"ok"}` |
| `/ready` | 200 | `{"status":"ready","service":"gamestory-logai-api","environment":"test"}` |

This confirms connection failure occurs before route SQL executes. It does not
test password rotation recovery, pool replacement, or transaction survival;
those features do not exist yet. No UAT access or production credentials were
used. ASGI transport captured the HTTP response; production server logging was
not tested.

## Requirement conflict and decision

FR-03 requires structured SQLSTATE detection during connection establishment.
The pinned psycopg driver exposes neither the SQLSTATE nor `InvalidPassword`
for this failure. Wrapping it in SQLAlchemy cannot restore the missing field.
The behavior is also documented by the psycopg maintainer in
[psycopg issue 1188](https://github.com/psycopg/psycopg/issues/1188) and the
[PostgreSQL discussion](https://www.postgresql.org/message-id/CA%2Bmi_8ZRi-NJsOw5SFUMXACLm-OFoS%2BDeRV3_5m7RgHfPXx1gg@mail.gmail.com).

Before implementation, select one of:

1. Preserve FR-03 and evaluate a synchronous driver exposing startup SQLSTATE,
   then migrate the common database boundary and driver-specific route usage.
   SQLAlchemy supports pg8000, which is a candidate to evaluate, not yet
   validated here. Preserve host/port/database/user/TLS semantics explicitly;
   libpq URL options are not automatically portable between drivers.
2. Retain psycopg and explicitly revise FR-03 to permit a tightly scoped
   authentication fallback. A message-only check does not satisfy the current
   PRD. Generic OperationalError, password-used flags, or a changed file alone
   must not be misrepresented as proof of SQLSTATE 28P01.

The PRD asks engineering to report significant architectural conflicts before
refactoring. The findings above were reported before implementation.
On 2026-10-29 the user approved retaining psycopg and tightening FR-03 with a
restricted missing-SQLSTATE fallback. The handover PRD now records the revised
requirement. The companion API implementation and platform Secret mounts follow
that decision; see `docs/database-credential-recovery.md` for the final design
and `docs/evidence/database-credential-recovery/` for local validation.

## Proposed implementation after the decision

Introduce a startup-loaded password provider and process-local engine manager.
Read the mounted file afresh only at startup and after confirmed authentication
failure; do not poll or retain descriptors. Explicitly retain a local URL mode.

Track acquisition reservations and checked-out contexts by generation. On
authentication failure before yielding a connection, coordinate refresh with a
bounded lock, recheck the generation, apply failure backoff, skip equivalent
credentials, and validate a candidate before publishing it. Bound pool waits,
connection establishment, and validation SQL time as well as lock acquisition.

Retired generations accept no new reservations; dispose only after their
existing reservations and transactions finish. A failed candidate is disposed
without replacing the active generation. Commit/rollback remains in the normal
context lifecycle. Never retry yielded business work or external operations.
SQLAlchemy's [engine disposal guidance](https://docs.sqlalchemy.org/en/20/core/connections.html#engine-disposal)
supports waiting for checked-out connections to return before disposal.

Add sanitized structured events and metrics, controlled unavailable responses,
and a read-only directory Secret mount without subPath. Reference-chart settings
should follow its existing `externalDatabase` / `postgres` Secret selection.
Provide a separate Schneider transfer patch using that chart's `database`
values once the actual template is available. Do not change ESO/IAM/AWS resources.

Required validation remains the PRD's real PostgreSQL rotation, concurrent
failures, stale/missing/unreadable files, failed candidates, unrelated errors,
active-transaction completion, and exactly-once external-call tests, followed
by Helm rendering and independent validation. Schneider must separately confirm
ESO synchronization, the current database topology, and mount rollout timing.
