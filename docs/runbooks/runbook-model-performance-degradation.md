# Runbook: Model Performance Degradation

## Trigger
Approved performance, score-distribution, drift, calibration, or outcome threshold is breached.

## Severity
High for material missed fraud or review overload; critical if decisions are unsafe or uncontrolled.

## Initial Checks
Validate labels, delay, population, model/version, threshold, features, slices, and monitoring calculation.

## Containment
Increase human review, constrain traffic, use approved fallback/rules, or roll back; never retrain automatically.

## Investigation
Analyse data drift, concept change, pipeline defects, adversarial behaviour, threshold effects, and affected groups.

## Remediation
Fix pipeline defects or develop a separately validated candidate model/threshold through full approval.

## Validation
Repeat temporal evaluation, calibration, error/slice, explainability, fairness, security, and load checks.

## Escalation
Model owner, Model Risk, Fraud Operations, MLOps, Data Engineering, and senior risk owner.

## Evidence to Retain
Predictions, labels, metrics, slices, versions, alerts, approvals, deployment/rollback records.

## Post-Incident Review
Reassess monitoring thresholds, label strategy, fallback readiness, and model expiry.
