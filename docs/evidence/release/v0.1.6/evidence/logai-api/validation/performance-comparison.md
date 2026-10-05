# Performance comparison

Sequential HTTP requests, 100 samples per endpoint; startup is one observation including container launch. Resource snapshots are retained in each adjacent `resources.json`. Results are diagnostic, not statistical proof. Compare on the same host and investigate material regressions before release.

| Metric | Source baseline | Compiled/runtime | Change |
|---|---:|---:|---:|
| Startup (ms) | 1786.72 | 1766.63 | -1.1% |
| Image size (bytes) | 210457332.00 | 201114228.00 | -4.4% |
| /health p50_ms | 1.27 | 1.26 | -0.8% |
| /health p95_ms | 1.42 | 1.48 | +4.2% |
| /health p99_ms | 2.05 | 2.02 | -1.4% |
| /api/v1/release p50_ms | 11.16 | 11.25 | +0.8% |
| /api/v1/release p95_ms | 12.72 | 12.70 | -0.2% |
| /api/v1/release p99_ms | 13.57 | 13.00 | -4.2% |
| /api/v1/chutes p50_ms | 11.42 | 11.72 | +2.6% |
| /api/v1/chutes p95_ms | 12.70 | 12.89 | +1.5% |
| /api/v1/chutes p99_ms | 13.14 | 13.78 | +4.9% |

Baseline resources:
```json
{"BlockIO":"0B / 0B","CPUPerc":"0.10%","Container":"logai-acceptance-dd07bd17","ID":"3738d97b6921","MemPerc":"0.71%","MemUsage":"56.15MiB / 7.751GiB","Name":"logai-acceptance-dd07bd17","NetIO":"1.66MB / 1.81MB","PIDs":"6"}

```

Candidate resources:
```json
{"BlockIO":"0B / 0B","CPUPerc":"0.12%","Container":"logai-acceptance-b9caaf3d","ID":"32b5b3966ce2","MemPerc":"0.71%","MemUsage":"56.25MiB / 7.751GiB","Name":"logai-acceptance-b9caaf3d","NetIO":"1.66MB / 1.81MB","PIDs":"6"}

```
