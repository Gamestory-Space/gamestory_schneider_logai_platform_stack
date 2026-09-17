# Platform testing

## Gamestory WSL2 and Podman

Build and release validation run on WSL2. Prerequisites are Ubuntu on WSL2, Podman, a Compose provider available through `podman compose`, and `curl`.

Pull-only release test:

```bash
cp environments/release/compose.env.example environments/release/compose.env
# Replace local password placeholders.
./scripts/test-wsl-podman.sh environments/release/compose.env
```

For a source build, use the Gamestory-only override:

```bash
podman compose -f compose.yaml -f compose.build.yaml \
  --env-file environments/build/compose.env.example up -d --build
```

## Gamestory local Kubernetes

Use k3s or another local Kubernetes distribution inside WSL2. Confirm the active local context before opting in:

```bash
kubectl config current-context
ALLOW_LOCAL_K8S_DEPLOY=yes ./scripts/test-local-kubernetes.sh release
```

This path validates the same Helm chart used by Schneider without requiring access to Schneider AWS.

## Schneider AWS

Client-local uses pull-only Compose. UAT and production use EKS and RDS. Schneider configures access with:

```bash
aws eks update-kubeconfig --name <cluster> --region <region>
kubectl config current-context
```

The client deployment script refuses a Kubernetes context that is not an AWS EKS ARN.
