# PRD-002 - Order Orchestration Platform Wiring

## Goal

Define the phase 1 platform wiring for the Schneider order orchestration use case.

## Scope

- Keep `logai-api` as the orchestration instigator.
- Add mock source service to the local/demo platform stack.
- Wire `logai-api` to SignalAutobahn, Agentic Core, Teams Interface, and database.
- Exclude simulation backend integration for phase 1; simulation UI remains present only as UI.

## Runtime Shape

```text
logai-ui
  -> logai-api
      -> signal-autobahn
          -> mock-schneider-sources
              -> SynQ allocation mock
              -> Cognos zone detail mock
      -> agentic-core
      -> teams-interface
      -> postgres
```

## Acceptance Criteria

- Platform docs identify the image/pod set for this use case.
- Local/demo compose can include mock source service.
- Schneider-side deployment remains responsible for real environment overrides.
