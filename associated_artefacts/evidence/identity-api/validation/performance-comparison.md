# Performance comparison

Sequential HTTP requests, 100 samples per endpoint; startup is one observation including container launch. Resource snapshots are retained in each adjacent `resources.json`. Results are diagnostic, not statistical proof. Compare on the same host and investigate material regressions before release.

| Metric | Source baseline | Compiled/runtime | Change |
|---|---:|---:|---:|
| Startup (ms) | 1313.39 | 1209.41 | -7.9% |
| Image size (bytes) | 197682980.00 | 188184170.00 | -4.8% |
| /health p50_ms | 1.00 | 0.99 | -0.5% |
| /health p95_ms | 1.14 | 1.10 | -3.9% |
| /health p99_ms | 1.78 | 1.27 | -28.4% |
| /config p50_ms | 0.96 | 0.96 | +0.3% |
| /config p95_ms | 1.03 | 1.05 | +2.4% |
| /config p99_ms | 1.04 | 1.07 | +2.9% |

Baseline resources:
```json
{"BlockIO":"0B / 0B","CPUPerc":"0.10%","Container":"logai-acceptance-bafb6946","ID":"b6772aac23b0","MemPerc":"0.53%","MemUsage":"41.8MiB / 7.751GiB","Name":"logai-acceptance-bafb6946","NetIO":"111kB / 159kB","PIDs":"6"}

```

Candidate resources:
```json
{"BlockIO":"0B / 0B","CPUPerc":"0.11%","Container":"logai-acceptance-b3c4a6c6","ID":"0059567e2df6","MemPerc":"0.53%","MemUsage":"41.84MiB / 7.751GiB","Name":"logai-acceptance-b3c4a6c6","NetIO":"112kB / 159kB","PIDs":"6"}

```
