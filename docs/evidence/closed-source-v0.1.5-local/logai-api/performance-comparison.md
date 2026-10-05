# Performance comparison

Sequential HTTP requests, 100 samples per endpoint; startup is one observation including container launch. Resource snapshots are retained in each adjacent `resources.json`. Results are diagnostic, not statistical proof. Compare on the same host and investigate material regressions before release.

| Metric | Source baseline | Compiled/runtime | Change |
|---|---:|---:|---:|
| Startup (ms) | 1141.38 | 1062.00 | -7.0% |
| Image size (bytes) | 188722126.00 | 189747617.00 | +0.5% |
| /health p50_ms | 0.87 | 0.88 | +1.8% |
| /health p95_ms | 1.36 | 1.56 | +15.0% |
| /health p99_ms | 1.83 | 2.32 | +27.0% |
| /api/v1/release p50_ms | 7.73 | 8.25 | +6.8% |
| /api/v1/release p95_ms | 9.57 | 9.78 | +2.2% |
| /api/v1/release p99_ms | 10.24 | 10.40 | +1.5% |
| /api/v1/chutes p50_ms | 8.07 | 8.17 | +1.2% |
| /api/v1/chutes p95_ms | 9.74 | 10.55 | +8.4% |
| /api/v1/chutes p99_ms | 10.57 | 11.82 | +11.9% |

Baseline resources:
```json
{"AvgCPU":52.62948821852529,"ContainerID":"5fa1f43e614c89fe829ad28fa37967dac22c56e2679b0edf50238b713c2a484f","Name":"logai-acceptance-65d7463e","PerCPU":null,"CPU":52.62948821852529,"CPUNano":1458313000,"CPUSystemNano":175160,"SystemNano":1790972034937933467,"MemUsage":60907520,"MemLimit":8188014592,"MemPerc":0.7438618888089056,"Network":{"eth0":{"RxBytes":1522303,"RxDropped":0,"RxErrors":0,"RxPackets":2573,"TxBytes":396667,"TxDropped":0,"TxErrors":0,"TxPackets":3186}},"BlockInput":0,"BlockOutput":0,"PIDs":6,"UpTime":1458313000,"Duration":1458313000}

```

Candidate resources:
```json
{"AvgCPU":51.41847517758723,"ContainerID":"2297094998f10bc1b9b55287ef797bada48cc28589bdcd1e52eaf710de32eceb","Name":"logai-acceptance-efa72f28","PerCPU":null,"CPU":51.41847517758723,"CPUNano":1508169000,"CPUSystemNano":247101,"SystemNano":1791035742450501681,"MemUsage":59445248,"MemLimit":8188014592,"MemPerc":0.726003200557071,"Network":{"eth0":{"RxBytes":1522441,"RxDropped":0,"RxErrors":0,"RxPackets":2574,"TxBytes":396667,"TxDropped":0,"TxErrors":0,"TxPackets":3186}},"BlockInput":0,"BlockOutput":0,"PIDs":6,"UpTime":1508169000,"Duration":1508169000}

```
