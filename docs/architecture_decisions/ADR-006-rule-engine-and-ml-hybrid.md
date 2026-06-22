# ADR-006: Hybrid Rule Engine and ML

## Status
Accepted architectural principle.

## Context
Financial-crime detection needs predictive ranking and transparent policy/scenario controls; neither approach is sufficient alone.

## Decision
Combine independently governed fraud ML, AML scenarios, customer risk components, and human investigation.

## Alternatives Considered
Rules-only systems are explainable but rigid; ML-only systems can obscure policy intent and miss explicit scenarios.

## Consequences
Overlapping alerts and false positives require reconciliation, calibration, case prioritisation, and clear ownership.

## Security Implications
Protect model artifacts, rule configuration, thresholds, and alert evidence from unauthorised changes.

## Cost Implications
Parallel controls add compute and review workload; staged filtering and batch evaluation can contain cost.

## Local Implementation Mapping
The fraud pipeline, ten AML rules, customer score, reason codes, and case outputs remain separately auditable.

## Azure Production Mapping
Managed endpoints provide scores; Stream Analytics/Functions or scheduled jobs execute rules; Synapse joins evidence for cases.
