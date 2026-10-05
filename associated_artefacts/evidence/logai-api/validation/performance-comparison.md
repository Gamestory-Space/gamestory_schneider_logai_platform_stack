# Performance comparison

Sequential HTTP requests, 100 samples per endpoint; startup is one observation including container launch. Resource snapshots are retained in each adjacent `resources.json`. Results are diagnostic, not statistical proof. Compare on the same host and investigate material regressions before release.

| Metric | Source baseline | Compiled/runtime | Change |
|---|---:|---:|---:|
| Startup (ms) | 1784.48 | 1823.50 | +2.2% |
| Image size (bytes) | 210457332.00 | 201114228.00 | -4.4% |
| /health p50_ms | 1.51 | 1.52 | +1.0% |
| /health p95_ms | 1.67 | 1.68 | +0.8% |
| /health p99_ms | 1.76 | 2.28 | +29.4% |
| /api/v1/release p50_ms | 14.78 | 15.23 | +3.0% |
| /api/v1/release p95_ms | 16.49 | 16.71 | +1.3% |
| /api/v1/release p99_ms | 17.07 | 17.06 | -0.1% |
| /api/v1/chutes p50_ms | 15.75 | 16.48 | +4.6% |
| /api/v1/chutes p95_ms | 17.13 | 20.75 | +21.1% |
| /api/v1/chutes p99_ms | 17.33 | 21.86 | +26.1% |

Baseline resources:
```json
{"BlockIO":"0B / 0B","CPUPerc":"0.11%","Container":"logai-acceptance-b605611a","ID":"698a5d0edf3e","MemPerc":"0.71%","MemUsage":"56.24MiB / 7.752GiB","Name":"logai-acceptance-b605611a","NetIO":"1.66MB / 1.81MB","PIDs":"6"}

```

Candidate resources:
```json
{"BlockIO":"0B / 0B","CPUPerc":"0.12%","Container":"logai-acceptance-ba85beff","ID":"2cb815a89f77","MemPerc":"0.71%","MemUsage":"56.25MiB / 7.752GiB","Name":"logai-acceptance-ba85beff","NetIO":"1.66MB / 1.81MB","PIDs":"6"}

```
