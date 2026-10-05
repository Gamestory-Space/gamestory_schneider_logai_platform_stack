# v0.1.7 login defaults

New installations in client-local, UAT and production create the configured users with password `logai_<username>`: Chris uses `logai_chris`, Elvis `logai_elvis`, Beau `logai_beau`, and Sunil `logai_sunil`. These are usable passwords without a mandatory first-login change. Keycloak administrator username is `admin`, password `chris`.

Compose sets `KEYCLOAK_BOOTSTRAP_PASSWORD_MODE=username`. Helm uses `identityBootstrap.passwordMode: username` and creates the administrator Secret when `keycloak.existingAdminSecret` is empty. Existing external administrator Secrets override the chart default. Database credentials remain independent runtime configuration.

For a temporary shared initial password, explicitly choose `shared` mode and provide the runtime user-password env value or mounted Secret. Existing accounts and changed passwords are preserved during reconciliation. Existing deployments require an explicit administrator password reset to adopt these defaults; updating env/Helm values does not reset existing credentials.

The handover extracts deployment files at the project root and evidence under `associated_artefacts/`. Private runtime env files are excluded.
