# Helm Overrides

The first environment override is `remote-build-dev`.

This represents our current remote/build/dev environment, effectively the dev-box setup used to build and validate the Schneider image set before handover.

```text
environments/
  remote-build-dev/
    values.example.yaml
    secrets.example.yaml
```

Create local, ignored copies when deploying from this workstation:

```powershell
Copy-Item environments/remote-build-dev/values.example.yaml environments/remote-build-dev/values.yaml
Copy-Item environments/remote-build-dev/secrets.example.yaml environments/remote-build-dev/secrets.yaml
```

`values.yaml` captures environment intent:

- image repositories and tags
- whether mock sources are enabled
- Keycloak public URLs and realm/client names
- local Entra tenant/client IDs
- local Teams app/tenant IDs
- Teams secret names for passwords
- Agentic Core config mount names

`secrets.yaml` or Vault-backed secret manifests capture runtime secret material and are ignored by git.

`secrets.example.yaml` captures the expected secret keys without real values:

- Entra client secret
- Microsoft Teams bot password
- Postgres connection URL

Real secret values must be created in the target environment and must not be committed.

Future Schneider-side deployment repos can follow the same structure:

```text
environments/
  build-dev/
    values.yaml
    secrets.references.yaml
  uat/
    values.yaml
    secrets.references.yaml
  prod/
    values.yaml
    secrets.references.yaml
```

The chart path is:

```text
helm/gamestory-schneider-platform
```

Example install command:

```bash
helm upgrade --install gamestory-platform ./helm/gamestory-schneider-platform \
  -f environments/remote-build-dev/values.yaml
```
