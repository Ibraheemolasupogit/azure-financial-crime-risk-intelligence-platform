# Runbook: Data Quality Failure

## Trigger
Critical schema, null, duplicate, relationship, range, volume, or freshness control fails.

## Severity
High when downstream decisions may be wrong; critical for widespread corruption or loss.

## Initial Checks
Confirm control, source, time window, batch/event IDs, recent schema/config/code changes, and monitoring integrity.

## Containment
Quarantine affected data, stop publication/scoring where unsafe, preserve raw events, and prevent checkpoint advancement if replay is required.

## Investigation
Trace producer-to-output lineage; compare known-good schemas/distributions and identify affected decisions.

## Remediation
Correct source or transformation through reviewed change; backfill idempotently from trusted raw data.

## Validation
Rerun quality, reconciliation, downstream regression, and lineage checks before release.

## Escalation
Data owner, Financial Crime Operations, MLOps, Security/Privacy, and incident command according to impact.

## Evidence to Retain
Payload hashes/samples, control results, logs, versions, approvals, affected outputs, and replay manifest.

## Post-Incident Review
Document cause, impact, control effectiveness, ownership, actions, and target dates.
