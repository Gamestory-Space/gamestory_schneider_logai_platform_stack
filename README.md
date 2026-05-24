# Gamestory Schneider Logai Platform Stack

Customer/platform stack repo for bringing the Schneider Logai deployment together.

This repo is intentionally light for now. The immediate work is to validate:

1. `logai-ui`
2. `gamestory-logai-api`
3. identity integration

After that, this repo should own the Schneider stack composition, runbooks, environment templates, smoke tests, and service wiring for SignalAutobahn, Agentic Core, Simulation, Teams, and external-system mocks.

Schneider-specific identity setup lives in:

```text
identity/schneider.identity.env.example
docs/schneider-identity.md
docs/schneider-logai-identity-integration.md
```

Generic identity templates and scripts remain in `gamestory-identity-kit`.

## Intended Stack Shape

```text
logai-ui
  -> gamestory-logai-api
      -> gamestory-signal-autobahn
          -> gamestory_agentic_core
          -> gamestory_simulation
          -> gamestory_teams_interfacing
          -> mock WMS / SynQ / Cognos
```
