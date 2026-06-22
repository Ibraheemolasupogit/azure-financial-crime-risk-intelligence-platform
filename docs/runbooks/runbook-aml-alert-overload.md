# Runbook: AML Alert Overload

## Trigger
Alert volume, concentration, queue age, duplicate rate, or investigator capacity exceeds approved thresholds.

## Severity
Medium for transient load; high when review SLAs or material-risk coverage are threatened.

## Initial Checks
Confirm rule versions, data volume/quality, dominant scenarios, duplication, geography/channel shifts, and queue capacity.

## Containment
Preserve alerts, add authorised capacity, deduplicate technical repeats, and prioritise by approved risk policy; do not silently suppress controls.

## Investigation
Separate true volume change, data defect, threshold/config change, replay duplication, and scenario overlap.

## Remediation
Correct defects or propose evidenced rule tuning through AML governance and validation.

## Validation
Back-test coverage, false-positive proxies, affected populations, queue projections, and reconciliation.

## Escalation
AML Operations, rule owner, ML/Data Engineering, Compliance, and senior financial-crime officer.

## Evidence to Retain
Rule/evidence versions, alert counts, queue snapshots, tuning analysis, approvals, and disposition outcomes.

## Post-Incident Review
Review capacity planning, scenario overlap, prioritisation, and detection-risk trade-offs.
