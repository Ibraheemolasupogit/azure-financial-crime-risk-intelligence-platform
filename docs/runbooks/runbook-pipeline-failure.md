# Runbook: Pipeline Failure

## Trigger
Scheduled or streaming stage fails, stalls, breaches latency, loses lineage, or produces incomplete outputs.

## Severity
Based on affected decisions, backlog, recoverability, and reporting obligations.

## Initial Checks
Locate failed stage/run, dependency state, identity/network errors, quota, storage, recent release, and last good checkpoint.

## Containment
Pause dependent publication, retain events, isolate bad release, scale only within approval, and communicate stale-data status.

## Investigation
Trace correlation IDs through logs, inputs, versions, checkpoints, resource health, and control outputs.

## Remediation
Roll back or fix through CI; replay idempotently from trusted checkpoint and reconcile counts.

## Validation
Complete pipeline, quality, lineage, latency, duplicate, downstream, and monitoring checks.

## Escalation
Platform Operations, Data/ML Engineering, service owner, Security when relevant, and business stakeholders.

## Evidence to Retain
Run IDs, logs, resource telemetry, versions, checkpoint/replay manifests, approvals, and reconciliations.

## Post-Incident Review
Address resilience, dependency, capacity, alerting, and recovery-test gaps.
