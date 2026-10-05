# Performance comparison

Sequential HTTP requests, 100 samples per endpoint; startup is one observation including container launch. Resource snapshots are retained in each adjacent `resources.json`. Results are diagnostic, not statistical proof. Compare on the same host and investigate material regressions before release.

| Metric | Source baseline | Compiled/runtime | Change |
|---|---:|---:|---:|
| Startup (ms) | 1288.99 | 1251.18 | -2.9% |
| Image size (bytes) | 197682296.00 | 188180074.00 | -4.8% |
| /health p50_ms | 1.24 | 1.24 | +0.2% |
| /health p95_ms | 1.34 | 1.36 | +1.4% |
| /health p99_ms | 1.42 | 1.40 | -1.3% |
| /config p50_ms | 1.27 | 1.27 | +0.4% |
| /config p95_ms | 1.36 | 1.37 | +0.4% |
| /config p99_ms | 1.42 | 1.39 | -2.2% |

Baseline resources:
```json
{"BlockIO":"0B / 0B","CPUPerc":"0.10%","Container":"logai-acceptance-ead8abee","ID":"a209336eb481","MemPerc":"0.54%","MemUsage":"42.58MiB / 7.752GiB","Name":"logai-acceptance-ead8abee","NetIO":"110kB / 160kB","PIDs":"6"}

```

Candidate resources:
```json
{"BlockIO":"0B / 0B","CPUPerc":"0.07%","Container":"logai-acceptance-21ce5a99","ID":"249a756000bb","MemPerc":"0.52%","MemUsage":"41.59MiB / 7.752GiB","Name":"logai-acceptance-21ce5a99","NetIO":"109kB / 161kB","PIDs":"6"}

```
