# Cost and Scalability

Local development uses workstation resources and free open-source dependencies. No Azure consumption is required by this repository.

| Area | Cost and scale drivers | Controls |
| --- | --- | --- |
| Event Hubs | Throughput/processing units, partitions, retention, Capture | Batch producers, right-size units, monitor lag/hot partitions |
| ADLS Gen2 | Capacity, transactions, redundancy, tier, egress | Lifecycle tiers, compact files, partitioning, retention |
| Synapse | Serverless bytes scanned or dedicated capacity/runtime | Curated columnar data, workload schedules, start serverless |
| Azure ML | Training VM type/time, parallel trials, batch compute | Autoscale-to-zero, quotas, spot where suitable, bounded tuning |
| Managed endpoints | Instance type/count, idle replicas, traffic | Autoscaling, batching, scale-to-zero alternatives for non-real-time |
| Azure OpenAI | Model/token volume, prompt size, evaluations, provisioned throughput | Evidence minimisation, caching where lawful, quotas, budget alerts |
| Power BI | User licensing, capacity, refresh, model size/concurrency | Aggregations, incremental refresh, workspace rationalisation |
| Purview | Data map capacity and scans | Risk-based scope/cadence, avoid redundant scans |
| Log Analytics | Ingestion, retention, queries, export | Sampling where safe, diagnostic categories, retention tiers |
| Networking | Private endpoints, firewall, NAT, egress | Shared governed topology and explicit egress paths |

Scale transactions by account-based partitioning, idempotent parallel consumers, date/tenant partitions, columnar formats, and incremental processing. Use asynchronous batch paths for retrospective AML and reporting while reserving online compute for latency-sensitive fraud decisions. Development/test resources should autoscale or shut down outside approved windows. Exact prices are intentionally omitted because region, agreement, date, tier, and architecture materially change them.
