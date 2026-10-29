# PRD — LogAI API: Dynamic Database Credential Rotation Recovery

**Project:** Schneider Electric — LogAI
**Component:** `logai-api`
**Priority:** High — UAT / Production readiness
**Implementation owner:** Codex Engineer
**Validation:** Independent Validator — Sofia AI Wong
**Status:** Implemented and locally validated; independent validation and Schneider rollout pending. FR-03 clarified with user approval 2026-10-29
**Target:** Existing AWS EKS deployment managed through Helm and Argo CD

---

## 1. Objective

Enable LogAI API to recover automatically when its PostgreSQL database password rotates in AWS Secrets Manager, **without restarting the API pod and without deliberately interrupting active database transactions**.

The solution must use Kubernetes-mounted Secret files, detect PostgreSQL password authentication failures, refresh the credentials and safely replace the SQLAlchemy connection pool.

The application must remain unaware of credential rotation until a database connection encounters an authentication failure.

## 2. Existing architecture

The Schneider environment uses:

- AWS RDS PostgreSQL.
- AWS Secrets Manager, with password rotation approximately every seven days.
- External Secrets Operator (ESO), expected to synchronise AWS credentials into Kubernetes.
- EKS namespace `68225-logai-uat`.
- Kubernetes Secret `logai-db-secret`, key `password`.
- Helm deployments managed through Schneider Argo CD.
- LogAI API implemented in Python/FastAPI.
- Keycloak using the same PostgreSQL database credentials.

The database currently uses:

- Database: `logai_dev`
- Username: `logai_dev_adm`
- SSL mode: `require`

The database host and other environment-specific settings must continue to come from existing Helm values.

**Engineering prerequisite:** Confirm that ESO is actually synchronising the correct AWS secret into `logai-db-secret`. This is Schneider-managed infrastructure, not an implementation responsibility for Codex.

## 3. Scope and ownership

### In scope

1. Add a Kubernetes Secret volume mount to the LogAI API Deployment.
2. Introduce a credential provider that can read the mounted password file.
3. Detect PostgreSQL authentication error `SQLSTATE 28P01`.
4. Refresh credentials only after an authentication failure.
5. Create and validate a replacement SQLAlchemy engine/connection pool.
6. Atomically direct new database sessions to the replacement pool.
7. Preserve existing sessions and active transactions during pool replacement.
8. Implement concurrency protection, safe failure handling, logging and tests.
9. Update deployment configuration and technical documentation.

### Out of scope

- AWS Secrets Manager configuration.
- External Secrets Operator installation or configuration.
- AWS IAM / EKS Pod Identity configuration.
- Changes to database password rotation policy.
- Keycloak application modifications.
- Keycloak pod restart automation.
- Automatic replay of warehouse business operations or SynQ requests.

Keycloak will use a separate controlled pod restart mechanism after password rotation.

## 4. Target architecture

```text
AWS Secrets Manager
        |
        | Password rotation (~7 days)
        v
External Secrets Operator
        |
        | Schneider-managed synchronisation
        v
Kubernetes Secret: logai-db-secret
        |
        | Kubernetes kubelet updates mounted volume
        v
/var/run/secrets/logai-db/password
        |
        | Read only when required
        v
LogAI API Credential Provider
        |
        | SQLSTATE 28P01 triggers recovery
        v
SQLAlchemy Engine / Pool Manager
        |
        +---- Existing generation: active transactions finish
        |
        +---- New generation: new database sessions
```

The mounted file must be the source of truth for runtime credential refresh.

No AWS SDK, direct Secrets Manager API calls or Kubernetes API access are required inside LogAI API.

## 5. Functional requirements

### FR-01 — Kubernetes Secret volume mount

Update the existing LogAI API Helm Deployment template, expected at:

`applications/logai/templates/20-logai-api.yaml`

Codex must first inspect the actual chart structure and preserve existing volume mounts, environment variables, health checks and security contexts.

Add a read-only Secret volume:

```yaml
volumes:
  - name: db-credentials
    secret:
      secretName: {{ .Values.database.secretName }}
      items:
        - key: password
          path: password
```

Add the corresponding container mount:

```yaml
volumeMounts:
  - name: db-credentials
    mountPath: /var/run/secrets/logai-db
    readOnly: true
```

Configure the password file path, preferably through a non-sensitive environment variable:

```yaml
- name: DATABASE_PASSWORD_FILE
  value: /var/run/secrets/logai-db/password
```

Requirements:

- Do not use `subPath`.
- Do not persist the password in a persistent volume.
- Do not embed credentials in Helm values.
- Ensure the application user can read the file under the existing container security context.
- Preserve existing deployment functionality.
- Support an explicit configuration mode for environments not yet using the Secret mount, if required by existing local development workflows.

**Deployment note:** Introducing the mount changes the Deployment pod template and will cause a one-time rolling rollout. This must be scheduled and validated separately from subsequent password rotations.

### FR-02 — Database credential provider

Introduce a small credential-provider abstraction responsible for obtaining the current database password.

Required behaviour:

- Read the password from `DATABASE_PASSWORD_FILE`.
- Open the file afresh on each refresh.
- Never cache an open file descriptor across refreshes.
- Never log the password or a password-bearing connection string.
- Handle missing files, unreadable files and empty values safely.
- Keep the password in process memory only, aside from the Kubernetes-managed Secret volume.

At initial application startup, read the current password and initialise the database engine.

During normal operations, do not poll the file.

### FR-03 — Authentication failure detection

Detect PostgreSQL authentication failure using:

`SQLSTATE 28P01 — invalid_password`

The detection must work through the actual database driver and SQLAlchemy exception wrapping used by the repository.

Prefer SQLSTATE `28P01` whenever the driver exposes it. For the existing pinned
psycopg/libpq driver, connection-startup authentication failures expose no SQLSTATE.
The user approved retaining psycopg and this narrowly scoped fallback on 2026-10-29:

- Apply detection only inside the application's configured `psycopg.connect()` call,
  before any connection has been yielded to business code.
- If SQLSTATE is present, it is authoritative; only `28P01` qualifies.
- Otherwise require a psycopg `OperationalError`, an attached failed PGconn for
  the configured database username, `used_password=true`, and the exact server
  `FATAL: password authentication failed for user "<configured username>"` message.
- Message matching alone, generic connection errors, and file changes do not qualify.
- Do not claim that this fallback received SQLSTATE `28P01` from the client driver.
- Unsupported/localized messages fail normally without credential refresh.

A recovered connection acquisition must continue the same request and then execute
its database transaction once. Healthy existing transactions retain their original
connections and finish normally. Never replay SQL, commits, route handlers, or
external calls after they have begun.

Credential refresh must not be triggered by:

- SQL syntax errors.
- Constraint violations.
- Database timeouts.
- Deadlocks.
- Generic connection failures.
- Authentication errors unrelated to the configured PostgreSQL credentials.

### FR-04 — Lazy credential refresh

When `SQLSTATE 28P01` is encountered during connection establishment:

1. Identify the current engine generation.
2. Acquire a concurrency-safe refresh lock.
3. Recheck whether another request has already replaced the failed generation.
4. If not, reread the password from the mounted Secret file.
5. Build a replacement SQLAlchemy engine using the latest credentials.
6. Validate the replacement engine using a lightweight database connection.
7. If validation succeeds, atomically publish the new engine generation.
8. Route newly created sessions to the replacement engine.
9. Retire the previous generation safely.

No application restart is permitted as part of credential recovery.

If the mounted password has not yet changed, do not repeatedly rebuild equivalent pools. Return a controlled database-unavailable error and permit a later request to attempt recovery after bounded backoff.

### FR-05 — Connection pool lifecycle

Implement safe management of multiple SQLAlchemy engine generations.

Requirements:

- Existing checked-out connections remain associated with their original engine.
- Existing sessions and transactions are not forcibly closed because of credential rotation.
- New sessions use the latest successfully validated engine.
- A failed candidate engine must never replace the active engine.
- Retired engines must be disposed of when no longer required.
- Avoid connection leaks and unbounded accumulation of retired pools.
- Protect engine-generation changes from concurrent requests.

Codex must inspect whether the application uses synchronous SQLAlchemy, asynchronous SQLAlchemy, or both, and implement the correct lifecycle for the existing architecture.

Do not assume a simple global `engine` reassignment is sufficient.

### FR-06 — Transaction integrity

**This is a mandatory acceptance gate.**

Credential recovery must not deliberately interrupt an active database transaction.

Rules:

- Do not close or invalidate healthy checked-out connections during pool replacement.
- Do not dispose of a pool in a way that disrupts active transactions.
- Do not automatically replay a transaction after an unknown or partial failure.
- Do not automatically repeat external side effects, including SynQ API calls.
- Only retry a connection-acquisition step when the implementation can establish that no business operation has begun.
- If a transaction has already failed, follow normal rollback and error-reporting behaviour.

Important limitation: PostgreSQL password rotation normally affects new authentication attempts, while existing authenticated connections may remain valid. The implementation must preserve these existing connections, but cannot guarantee transaction survival if the underlying connection itself fails.

### FR-07 — Concurrent recovery

Multiple requests may encounter authentication failures simultaneously.

The implementation must:

- Ensure only one refresh is performed for a failed engine generation within a worker.
- Prevent duplicate replacement pools from being published.
- Allow requests to observe a successfully refreshed generation.
- Avoid deadlocks and indefinite blocking.
- Use bounded timeouts and backoff.

If LogAI API runs multiple Python workers or replicas, each process may need to refresh its own engine independently. Do not assume an in-process lock coordinates all workers or pods.

### FR-08 — Failure handling

Handle the following conditions explicitly:

| Condition | Required behaviour |
|---|---|
| Password rotated, mounted file updated | Refresh pool and recover |
| Password rotated, mounted file still stale | Controlled failure; retry recovery on a later request |
| Mounted file missing | Preserve active pool; report configuration failure |
| Mounted file unreadable | Preserve active pool; report failure |
| Replacement connection fails | Do not publish candidate pool |
| Multiple requests fail concurrently | Single refresh per failed generation per worker |
| Existing transaction in progress | Allow existing connection to complete |
| Unrelated PostgreSQL error | Preserve existing error handling |
| Secret synchronisation permanently fails | Surface operational alert; avoid infinite retry loops |

### FR-09 — Observability

Add structured events and metrics for:

- Database authentication failure detected.
- Credential refresh started.
- Credential refresh succeeded.
- Credential refresh failed.
- Engine generation replaced.
- Old engine generation retired.
- Refresh duration.
- Number of recovery attempts.

Never log:

- Database passwords.
- Secret file contents.
- Password-bearing database URLs.
- AWS credentials.

Avoid exposing sensitive exception details in API responses.

## 6. Configuration

Proposed configuration keys:

| Setting | Suggested default | Purpose |
|---|---|---|
| `DATABASE_PASSWORD_FILE` | `/var/run/secrets/logai-db/password` | Mounted password location |
| `DB_CREDENTIAL_REFRESH_ENABLED` | `true` in UAT | Enables reactive recovery |
| `DB_CREDENTIAL_REFRESH_BACKOFF_SECONDS` | `5` | Prevents repeated failed refreshes |
| `DB_CREDENTIAL_REFRESH_MAX_WAIT_SECONDS` | `10` | Bounds waiting during recovery |

Codex should align these with existing configuration conventions and avoid unnecessary new settings.

Existing database host, port, name, username and SSL settings remain unchanged.

## 7. Testing and validation

### Unit tests

- Password file loads correctly.
- New password is read after file replacement.
- PostgreSQL `28P01` is recognised.
- Unrelated SQLSTATE values do not trigger refresh.
- Missing and empty files are handled.
- Concurrent refresh attempts are coordinated.
- Failed candidate engine does not replace the active engine.

### Integration tests

Use PostgreSQL with SQLAlchemy and the application's actual driver.

**Test A — Normal operation**

Start LogAI API with password P1. Verify database reads and writes succeed.

**Test B — Password rotation**

Change PostgreSQL password from P1 to P2 and update the mounted test Secret file.

Force a new database connection using stale P1.

Expected:

- Authentication failure detected.
- Password P2 loaded.
- Replacement engine validated.
- New database operations succeed.
- No API process restart.

**Test C — In-flight transaction**

Start a transaction using an existing authenticated connection.

Rotate the password and trigger recovery through another connection.

Expected:

- Existing transaction completes successfully.
- New connections use P2.
- No forced rollback or connection termination caused by pool replacement.

**Test D — Concurrent requests**

Generate multiple authentication failures simultaneously.

Expected:

- One effective pool-generation replacement per worker.
- No duplicate published engines.
- No deadlocks.
- No leaked connections.

**Test E — Secret propagation delay**

Rotate PostgreSQL password but leave the mounted file at P1 temporarily.

Expected:

- Initial recovery fails safely.
- Existing healthy transactions remain undisturbed.
- A subsequent recovery attempt succeeds once the file contains P2.

**Test F — SynQ safety**

Simulate a workflow involving a database transaction and an external SynQ request.

Expected:

- No duplicate SynQ request.
- No automatic replay of partially completed business operations.
- Existing error-handling and audit behaviour remain intact.

## 8. Implementation sequence

1. Inspect current database engine creation, session management, transaction boundaries and exception handling.
2. Document any architecture constraints or conflicts before editing.
3. Implement the credential provider.
4. Implement engine-generation management.
5. Implement `28P01` detection and reactive recovery.
6. Integrate the provider with all relevant database session creation paths.
7. Add Helm Secret volume mount and configuration.
8. Implement unit and integration tests.
9. Validate Helm rendering for the UAT environment.
10. Submit implementation evidence for independent validation.

Do not modify Schneider-managed ESO, IAM or Secrets Manager resources.

## 9. Deliverables

Codex must provide:

- Updated LogAI API source code.
- Updated Helm template and relevant values.
- Automated tests.
- A short implementation note explaining engine lifecycle and recovery.
- Evidence of successful password rotation recovery.
- Evidence that active transactions survive pool replacement.
- Any identified limitations or residual risks.
- Pull request for independent review.

## 10. Acceptance criteria

The change is acceptable when:

- [ ] LogAI API starts using the mounted Secret password.
- [ ] Existing database operations work normally.
- [ ] Password rotation does not require an API pod restart.
- [ ] `SQLSTATE 28P01` triggers credential refresh.
- [ ] A new, validated connection pool becomes active.
- [ ] Healthy in-flight transactions are not interrupted by pool replacement.
- [ ] No warehouse business transaction or SynQ operation is automatically replayed.
- [ ] Concurrent failures do not create uncontrolled pool replacements.
- [ ] Stale or missing Secret values fail safely.
- [ ] No database credentials appear in logs.
- [ ] Helm renders and deploys correctly.
- [ ] Independent validation passes.

## 11. Engineering instructions to Codex

Before implementation, inspect the repository and identify the actual database engine/session lifecycle. Do not assume the architecture matches the examples in this PRD.

Prefer the smallest maintainable implementation consistent with existing patterns.

If the current architecture makes safe engine replacement impossible without significant refactoring, report the issue and proposed changes before proceeding.

Do not introduce AWS SDK dependencies, Kubernetes API access, automatic pod restarts or automatic business-transaction retries.

**Final engineering principle:** LogAI API should operate normally without awareness of password rotation until a new database connection fails authentication. At that point it should refresh the mounted credential, replace the connection pool safely and recover without restarting the application or disrupting healthy in-flight transactions.
