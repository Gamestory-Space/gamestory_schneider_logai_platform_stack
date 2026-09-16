# Deployment Model

| Environment | Owner | Helm/GKE | Compose |
| --- | --- | --- | --- |
| build | Gamestory | Yes | Yes |
| release | Gamestory | Yes | Yes, pull only |
| client-local | Schneider/local | Yes; also local k3s | Yes, pull only |
| uat | Schneider | Yes | No |
| prod | Schneider | Yes | No |

Configuration precedence is chart defaults, environment values, delivery overrides, then runtime secrets. The placeholder GKE ingress, registry, DNS, secret, and database references in UAT and production must be replaced by Schneider-controlled values.
