# Client deployment bundle

CI publishes a client-only OCI image to Docker Hub:

```text
docker.io/chrismdgs/gamestory_logai_schneider:platform-bundle-<version>
```

The bundle contains only:

- Pull-only `compose.yaml`
- Helm chart
- `client-local`, `uat`, and `prod` overlays
- Schneider deployment and smoke-test scripts
- Client deployment documentation and identity example

It excludes the Gamestory `build` and `release` environments, source-build Compose override, source repositories, and application source.

Publish by pushing a version tag or manually running `Publish client deployment bundle`. CI requires `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` repository secrets.

Extract with Podman:

```bash
./scripts/extract-client-bundle.sh \
  docker.io/chrismdgs/gamestory_logai_schneider:platform-bundle-v0.2.0 \
  ./schneider-logai-deployment
```

The same script uses Docker when Podman is unavailable. The bundle image is a transport artifact and is not intended to run as a workload.
