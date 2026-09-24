# Gamestory Schneider LogAI Platform Stack

Canonical deployment repository for Postgres, Keycloak, Identity API, LogAI API, and LogAI UI. Helm is authoritative across all five source-repository environments. The published client ZIP contains only client-local, UAT, and production assets.

| Environment | Owner | Helm | Compose |
| --- | --- | --- | --- |
| build | Gamestory | Yes | Yes, source-build override |
| release | Gamestory | Yes | Yes, pull only |
| client-local | Schneider/local | Yes | Yes, pull only |
| uat | Schneider | Yes | No |
| prod | Schneider | Yes | No |

## Platform release archive

Release `v0.1.4` produces a signed, client-only ZIP and IREP evidence pack. The ZIP is pushed to Docker Hub as a generic OCI artifact, not as a runnable image. See `docs/platform-bundle.md`.

```bash
./scripts/package-client-release.sh v0.1.4 dist
```

## Validate

```bash
./scripts/helm-lint.sh
./scripts/helm-template.sh
./scripts/validate-client-bundle.sh
./scripts/test-client-release-policy.sh

docker compose -f compose.yaml -f compose.build.yaml --env-file environments/build/compose.env.example config
docker compose -f compose.yaml --env-file environments/release/compose.env.example config
docker compose -f compose.yaml --env-file environments/client-local/compose.env.example config
```

## Test

```bash
# WSL2 + Podman local test
cp environments/client-local/compose.env.example environments/client-local/compose.env
./scripts/test-wsl-podman.sh

# Gamestory local Kubernetes release test, after checking the active context
ALLOW_LOCAL_K8S_DEPLOY=yes ./scripts/test-local-kubernetes.sh release
```

## Build or deploy with Compose

```bash
# Gamestory source build
docker compose -f compose.yaml -f compose.build.yaml --env-file environments/build/compose.env.example up -d --build

# Pull-only release or client-local
docker compose -f compose.yaml --env-file environments/release/compose.env up -d --no-build
docker compose -f compose.yaml --env-file environments/client-local/compose.env up -d --no-build
```

## Helm

```bash
helm upgrade --install logai ./helm/gamestory-schneider-platform --namespace logai --create-namespace -f environments/client-local/values.yaml
```

See `docs/testing.md`, `docs/platform-bundle.md`, `docs/deployment-model.md`, and `docs/schneider-handoff.md`.

## Schneider branch strategy

The Schneider-owned repository uses three branch roles:

```text
Gamestory release
       |
       v
gamestory_rel<n>  (immutable inbound release)
       |
       | reviewed merge
       v
client             (Schneider integration and configuration)
       |
       | validated promotion pull request
       v
main               (approved deployable state)
       |
       +--> client-local Compose
       +--> UAT EKS
       +--> production EKS
```

### `gamestory_rel<n>`

Each Gamestory delivery creates a new numbered inbound branch, for example `gamestory_rel1`, `gamestory_rel2`, and `gamestory_rel3`.

- Import one released platform bundle or approved Gamestory release into the branch.
- Record the source commit, application image tags/digests, bundle version, and validation evidence in the pull request.
- Do not make Schneider-specific changes on this branch.
- Do not rewrite or reuse an earlier release branch.
- Protect the branch from force pushes and direct commits after import.

### `client`

This is Schneider's integration branch.

- Merge the selected `gamestory_rel<n>` branch through a reviewed pull request.
- Apply Schneider-owned configuration such as JFrog image references, AWS EKS/RDS settings, ingress, DNS, resource sizing, and secret references.
- Never commit passwords, tokens, certificates, private keys, or raw AWS credentials.
- Validate client-local Compose and render the UAT and production Helm configuration before promotion.
- Resolve new Gamestory release conflicts here, never on the immutable release branch.

### `main`

This branch represents the currently approved deployable state.

- Promote from `client` only through a reviewed pull request after validation and client acceptance.
- Do not merge a `gamestory_rel<n>` branch directly into `main`.
- Protect `main` with required reviews and CI checks; disable force pushes and direct commits.
- Tag each approved deployment baseline, for example `schneider-v1.0.0`.
- Deploy client-local, UAT, and production from an identified `main` commit or immutable tag, never from an unreviewed branch head.

### Release promotion

Example for the second Gamestory delivery:

```bash
git fetch --all --tags
git switch -c gamestory_rel2 <approved-gamestory-commit-or-tag>
git push -u origin gamestory_rel2

# Open and review: gamestory_rel2 -> client
# Apply and validate Schneider configuration on client.
# Open and review: client -> main
# Tag the approved main commit after acceptance.
```

Recommended gates before `client` is promoted to `main`:

```bash
helm lint ./helm/gamestory-schneider-platform
./scripts/helm-template.sh
docker compose --env-file environments/client-local/compose.env -f compose.yaml config --quiet
./scripts/validate-client-bundle.sh
```

UAT and production still require Schneider-controlled private values, runtime Secrets, AWS access, and the appropriate deployment approval.

### Hotfixes and rollback

- Make an urgent Schneider fix on a short-lived branch created from `main`.
- Merge the fix into `client` first, validate it, then promote it to `main` through the normal review gate.
- If operational urgency requires a direct main-targeting pull request, immediately merge the same fix back into `client` to prevent divergence.
- Roll back by redeploying the preceding approved `schneider-v*` tag and its recorded immutable application image digests.
