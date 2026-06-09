# Order Orchestration Flow

Phase 1 order orchestration keeps `logai-api` as the instigator and state owner.

Simulation is UI-only in this phase. There is no backend simulation call in this flow.

## Flow

1. Scheduler, operator action, or future UI command starts an orchestration run in `logai-api`.
2. `logai-api` initiates a SynQ allocation pull through `signal-autobahn`.
3. `signal-autobahn` calls the SynQ mock source and returns allocations to `logai-api`.
4. `logai-api` initiates a Cognos zone-detail pull through `signal-autobahn`.
5. `signal-autobahn` calls the Cognos mock source and returns order-zone detail to `logai-api`.
6. `logai-api` builds the global orchestration state for the run.
7. `logai-api` calls `agentic-core` for recommendation/reasoning.
8. `logai-api` persists source state, orchestration state, agentic result, and Teams state in Postgres.
9. For AS zone release:
   - `suggest` mode routes AS release through Teams.
   - `supervise` mode routes AS release through Teams.
   - `sentient` mode can skip Teams for AS release if policy allows.
10. `logai-api` calls `teams-interface` when Teams approval/notification is required.
11. `teams-interface` sends the Teams card/message and receives operator responses.
12. Teams responses come back to `logai-api` through callback/workflow routes and update the run state.

## Source Adapters

Only two phase 1 external source adapters are required:

- SynQ allocations
- Cognos reporting/order-zone detail

There is no direct WMS adapter in this phase. WMS-derived information is consumed through Cognos.

## Local Endpoint

Start a mock-backed orchestration run:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://localhost:8010/api/v1/order-orchestration/runs?tenantId=schneider&siteId=helmond" `
  -ContentType "application/json" `
  -Body '{"aiMode":"supervise"}'
```
