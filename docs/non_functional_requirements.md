# Non-Functional Requirements

The targets below are illustrative design inputs, not measured production SLOs or regulatory commitments.

| Quality | Illustrative target | Evidence/control |
| --- | --- | --- |
| Availability | Online scoring 99.9% monthly; batch reporting by agreed window | Multi-zone review, health probes, fallback/queue |
| Reliability | No acknowledged event loss; idempotent reprocessing | Capture, checkpoints, event IDs, reconciliations |
| Scalability | Sustain 10x baseline volume after load test | Partitioning, autoscaling, capacity tests |
| Performance | P95 fraud decision under 300 ms excluding producer network | Feature budget, endpoint telemetry, load tests |
| Batch latency | Curated daily outputs within 60 minutes of cutoff | Incremental jobs and pipeline SLOs |
| Security | No public data/model endpoints; no standing privileged access | Private access, PIM, RBAC, reviews |
| Privacy | Purpose-limited, minimised attributes; approved retention | Classification, DLP, deletion/hold workflows |
| Observability | 100% critical services emit health, security, and lineage signals | Diagnostic settings and control coverage |
| Maintainability | Reviewed modular changes; clear ownership/runbooks | CI, ADRs, code quality, service catalogue |
| Reproducibility | Same data/config/code/environment reproduces approved model | Immutable versions, seeds, manifests |
| Recoverability | Illustrative RTO 4h, RPO 15m for critical serving | Backup, replay, restoration exercises |
| Auditability | Decision evidence retrievable for approved retention period | Correlation IDs, immutable logs, lineage |
| Explainability | 100% scored decisions retain model/version and reason evidence | Reconstruction and completeness controls |
| Data quality | Critical contract failures block downstream publication | Validation, quarantine, ownership |
| Regulatory readiness | Traceable controls and evidence; no compliance claim | Legal/compliance gap assessment and testing |

Targets must be risk-assessed, negotiated with business owners, measured under realistic load, and reviewed by security, resilience, privacy, model-risk, financial-crime, and regulatory stakeholders.
