# Argo CD deployment

GitHub Actions remains the continuous integration mechanism for the individual LogAI application components. Those pipelines build and publish immutable, versioned UI, API, and Teams Bot container images to Schneider JFrog; this platform repository does not build those applications.

This repository declares the desired LogAI platform deployment. Its shared Helm chart composes the independently versioned application images and supporting Kubernetes resources. Argo CD reads that Helm definition from Git and reconciles it into Schneider EKS.

UAT and Production use the same chart at `helm/gamestory-schneider-platform`. They are distinguished by their environment-specific values files under `environments/` and by the cluster and namespace destinations in their respective Argo CD Applications:

- `logai-uat.yaml` uses `environments/uat/values.yaml` and the UAT destination.
- `logai-prod.yaml` uses `environments/prod/values.yaml` and the Production destination.

## Schneider onboarding

Before applying these definitions, Schneider's Argo team must replace every angle-bracketed placeholder and configure the referenced Argo AppProject to permit:

- the LogAI platform Git repository as a source;
- the UAT EKS cluster and LogAI UAT namespace as a destination; and
- the Production EKS cluster and LogAI Production namespace as a destination.

The Applications contain no repository, Argo, Rancher, cluster, or application credentials. Credentials and secrets must never be stored in this repository. Repository access and cluster access are configured in Schneider's Argo CD installation, while runtime secrets remain managed through Schneider-approved processes.

Namespaces must be provisioned through Schneider platform/Rancher processes. `CreateNamespace=false` prevents Argo CD from creating them.

Initial synchronization is intentionally manual. Automated synchronization, pruning, and self-healing may be enabled later only after Schneider confirms its governance and approval model.
