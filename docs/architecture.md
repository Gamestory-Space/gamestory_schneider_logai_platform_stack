# Architecture

The canonical first drop contains Postgres, Keycloak, Identity API, LogAI API, and LogAI UI. Helm is authoritative. Compose represents the same five workloads for build, release, and client-local only.

```text
Browser -> LogAI UI -> LogAI API -> Postgres
                |          |
                +-> Identity API -> Keycloak -> Postgres
```

SignalAutobahn, Agentic Core, Teams Interface, and Schneider adapters remain future extensions. Existing orchestration documents describe that future state but those services are not deployed by this chart.
