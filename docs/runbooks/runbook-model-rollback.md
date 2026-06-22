# Runbook: Model Rollback

## Trigger
Approved rollback criterion: performance, integrity, latency, security, explanation, fairness, or operational failure.

## Severity
High when active decisions are affected; coordinate as an incident change.

## Initial Checks
Confirm active endpoint/deployment/model/config, trigger evidence, previous approved version, schema compatibility, and traffic state.

## Containment
Stop promotion, route to known-good blue deployment or approved fallback, preserve current artifacts and requests.

## Investigation
Determine failure scope, affected predictions/cases, data compatibility, and whether rollback alone is sufficient.

## Remediation
Apply approved traffic change, restore matching feature/config versions, and reprocess eligible decisions under governance.

## Validation
Smoke/load tests, health, latency, prediction distributions, explanations, monitoring, and business-owner confirmation.

## Escalation
MLOps, model owner, Model Risk, Fraud/AML Operations, change manager, and Security if integrity-related.

## Evidence to Retain
Model/deployment versions, traffic changes, metrics, approvals, request IDs, affected decisions, and validation results.

## Post-Incident Review
Fix the candidate lifecycle, rollback automation, compatibility tests, and trigger thresholds.
