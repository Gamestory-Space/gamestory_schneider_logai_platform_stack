# Performance comparison

Sequential HTTP requests, 100 samples per endpoint; startup is one observation including container launch. Resource snapshots are retained in each adjacent `resources.json`. Results are diagnostic, not statistical proof. Compare on the same host and investigate material regressions before release.

| Metric | Source baseline | Compiled/runtime | Change |
|---|---:|---:|---:|
| Startup (ms) | 1303.62 | 875.92 | -32.8% |
| Image size (bytes) | 192841613.00 | 194267856.00 | +0.7% |
| /health p50_ms | 0.61 | 0.67 | +10.0% |
| /health p95_ms | 1.15 | 1.06 | -8.1% |
| /health p99_ms | 2.64 | 2.56 | -2.9% |
| /config p50_ms | 0.61 | 0.63 | +3.3% |
| /config p95_ms | 0.80 | 1.16 | +43.9% |
| /config p99_ms | 2.71 | 2.15 | -20.6% |

Baseline resources:
```json
{"AvgCPU":52.927768643629655,"ContainerID":"d5a0a4278df6ff24dd6578a22a7f8b515840e8e00c026cfcb7646fc3222f5ee9","Name":"logai-acceptance-446bfd30","PerCPU":null,"CPU":52.927768643629655,"CPUNano":722454000,"CPUSystemNano":140585,"SystemNano":1790972017066007240,"MemUsage":49242112,"MemLimit":8188014592,"MemPerc":0.6013925774889484,"Network":{"eth0":{"RxBytes":198,"RxDropped":0,"RxErrors":0,"RxPackets":3,"TxBytes":382,"TxDropped":0,"TxErrors":0,"TxPackets":5}},"BlockInput":0,"BlockOutput":0,"PIDs":6,"UpTime":722454000,"Duration":722454000}

```

Candidate resources:
```json
{"AvgCPU":64.75197792146152,"ContainerID":"d357d1e5e100e1b8fb7fadd28715cc54f5368e7fc6d313f716010cebc8f6ae68","Name":"logai-acceptance-34f7ac91","PerCPU":null,"CPU":64.75197792146152,"CPUNano":737274000,"CPUSystemNano":83240,"SystemNano":1791035731441850715,"MemUsage":44527616,"MemLimit":8188014592,"MemPerc":0.543814565786255,"Network":{"eth0":{"RxBytes":198,"RxDropped":0,"RxErrors":0,"RxPackets":3,"TxBytes":472,"TxDropped":0,"TxErrors":0,"TxPackets":6}},"BlockInput":0,"BlockOutput":0,"PIDs":6,"UpTime":737274000,"Duration":737274000}

```
