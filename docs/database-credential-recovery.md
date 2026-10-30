# Database credential recovery deployment

The companion `gamestory-logai-api` change implements mounted-password recovery
using psycopg and SQLAlchemy pool generations. FR-03 in the handover PRD now
records the user-approved, restricted missing-SQLSTATE fallback for libpq startup
authentication failures. See `docs/prd/PRD-008-database-credential-rotation-assessment.md`
for the initial reproduction and the API's `docs/database-credential-recovery.md`
for lifecycle, transaction, and timeout semantics.

## Reference chart

The actual local Deployment is `helm/gamestory-schneider-platform/templates/apps.yaml`.
Enable `logaiApi.databaseCredentials.enabled` with the provided
`environments/uat/database-credential-recovery.yaml` overlay **after building and
selecting an API image containing the companion source change**. Existing pinned
v0.1.7 images do not implement recovery, so base values retain disabled behavior.
No release tag/digest has been invented or replaced by this change.

The selected existing Secret comes from `externalDatabase.existingSecret` or
`postgres.existingSecret`. The password key follows the corresponding
`passwordKey`; the existing `databaseUrlKey` reference remains intact. The file
password overrides the stale environment URL password, preserving its host,
database, user, port, SSL, and other libpq options. ESO must update the password
key; updating only the URL key will not refresh the mounted password.

The volume mounts the whole directory `/var/run/secrets/logai-db`, read-only,
without subPath. Mode 0440 and the existing fsGroup 10001 allow the non-root API
user to read the projected file. Existing tmp/UI mounts, probes, environment,
service account, and container restrictions remain. No password checksum is
added to the pod template, so subsequent Secret updates do not request rollouts.
Introducing the mount and the new image causes a one-time rolling rollout.

Example render using a separately supplied image tag/digest:

```sh
helm template logai helm/gamestory-schneider-platform \
  --namespace 68225-logai-uat \
  -f environments/uat/values.yaml \
  -f environments/uat/database-credential-recovery.yaml
```

This renders reference placeholder database settings, not Schneider's actual
environment. Do not deploy without its actual existing Secret and image values.

## Schneider chart transfer

The PRD's `applications/logai/templates/20-logai-api.yaml` is absent locally.
Use the additive snippets in
`handover/schneider-argocd/database-credential-recovery.md` when adapting that
chart; do not replace the Schneider Deployment with the reference chart.
Render the real chart with actual UAT values before deployment. Confirmation
of ESO synchronization into `logai-db-secret/password`, namespace, current
database topology and username, and the scheduled initial rollout belongs to
Schneider. AWS/ESO/IAM and Keycloak resources are outside this change.

## Acceptance and operational limits

Validate normal reads/writes, fresh-connection failure after password rotation,
same-request continuation, unchanged API process, and commit of an open
transaction while another request refreshes the pool. Check concurrent failures
produce one replacement per worker and Secret propagation delays return safe
503 responses before later recovery. Do not manually terminate active database
connections to force rotation tests; exhaust/hold the idle pool in an isolated
test instead. Review `/metrics` refresh failures and durations; sustained stale
Secrets need an operational alert. `/ready` currently remains a static response
and does not prove database access. Liveness must not restart pods for rotation.

No route, SQL transaction, SynQ request, or Teams action is replayed. A failed
acquisition recovers before business SQL runs; healthy open transactions finish
on their old connections. A transaction whose actual connection fails cannot
be resumed automatically. Separate external effects already completed before
acquisition remain subject to existing audit/reconciliation behavior.

Local automated evidence does not certify Schneider deployment or independent
validator acceptance. A new API image must pass the existing release/SBOM gates
before UAT deployment; this change does not publish or deploy one.
