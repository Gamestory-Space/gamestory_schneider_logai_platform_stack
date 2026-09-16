# Local k3s

Target path:

```text
Windows -> WSL2 -> Ubuntu -> k3s -> Kubernetes -> Helm -> LogAI Platform
```

Install WSL2 and Ubuntu using the approved workstation process. This repository does not modify WSL configuration. In Ubuntu, install k3s and Helm, confirm `kubectl get nodes` reports `Ready`, import or make the three application images pullable, then run:

```bash
./scripts/helm-lint.sh
./scripts/helm-template.sh
./scripts/deploy-local.sh
./scripts/smoke-test.sh
```

For local images, import them into the k3s containerd image store or override the client-local repositories with a registry reachable by k3s.
