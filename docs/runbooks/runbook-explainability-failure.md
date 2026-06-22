# Runbook: Explainability Failure

## Trigger
Decision reconstruction, reason-code completeness, prohibited-feature, lineage, or investigator usability control fails.

## Severity
High when affected model decisions cannot be explained or audited.

## Initial Checks
Confirm model/preprocessor/version alignment, feature order, coefficients, prediction IDs, and output completeness.

## Containment
Stop publishing affected explanations, flag decisions for enhanced review, preserve model inputs/outputs, and avoid fabricated reasons.

## Investigation
Reconstruct scores independently and trace transformation mappings, serialization, schema, and model changes.

## Remediation
Fix mapping or model-package defects through reviewed release; regenerate explanations from retained evidence.

## Validation
Require numerical reconstruction, prohibited-field, reason ranking, sampled human review, and audit retrieval.

## Escalation
Model owner, Model Risk, Investigation Operations, MLOps, and Compliance where explanation obligations apply.

## Evidence to Retain
Inputs, transformed values, contributions, model/version, code/config, failed controls, and reviewer decisions.

## Post-Incident Review
Improve package contracts, compatibility tests, and explanation monitoring.
