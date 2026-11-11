# Additive LogAI API database credential recovery transfer

Apply to the existing Schneider LogAI API container/Deployment, preserving all
existing entries. The full target template is not in this repository; these
snippets are transfer instructions, not a replacement workload or runnable
patch. Use only with the new recovery-capable API image. Do not apply to Keycloak.

Add non-sensitive environment entries to the API container:

```yaml
- name: DATABASE_PASSWORD_FILE
  value: /var/run/secrets/logai-db/password
- name: DB_CREDENTIAL_REFRESH_ENABLED
  value: "true"
- name: DB_CREDENTIAL_REFRESH_BACKOFF_SECONDS
  value: "5"
- name: DB_CREDENTIAL_REFRESH_MAX_WAIT_SECONDS
  value: "10"
```

Retain the existing DATABASE_URL reference and its host/user/database/SSL
settings. Confirm that it references the same configured login as the mounted
password. Do not put credentials in Helm values or copy passwords into a PV.

Append to the API container's `volumeMounts`:

```yaml
- name: db-credentials
  mountPath: /var/run/secrets/logai-db
  readOnly: true
```

Append to the pod's `volumes`:

```yaml
- name: db-credentials
  secret:
    secretName: {{ .Values.database.secretName }}
    defaultMode: 0440
    items:
      - key: password
        path: password
```

Keep UID/GID/fsGroup 10001 and verify that user can read the projected file;
do not use subPath or add a password checksum rollout trigger. Configure
`database.secretName` to the Schneider-managed `logai-db-secret` only after its
owner confirms ESO updates the `password` key. No ESO/IAM/AWS change is supplied.

Render the complete Schneider chart with its UAT values and inspect the merged
Deployment, including existing mounts/security/probes, before the one-time
rollout. Observe an actual password rotation and transaction preservation after
deployment. Subsequent password updates require neither API restart nor rollout.
Keep Keycloak's separately controlled restart process unchanged.
