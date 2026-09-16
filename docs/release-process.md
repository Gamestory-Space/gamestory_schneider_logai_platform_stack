# Release process

Release validates the published artifacts intended for handoff. Set immutable version tags or digests in `environments/release/values.yaml`, authenticate to the registry, and deploy without building application source.

```bash
docker compose --env-file environments/release/compose.env pull
docker compose --env-file environments/release/compose.env up -d --no-build
helm upgrade --install logai ./helm/gamestory-schneider-platform -f environments/release/values.yaml --namespace logai --create-namespace
```

Record source revisions, image digests, validation evidence, and rollback versions. Never promote a mutable `latest` tag.
