# Explainability Governance

## Intended Use

Explanations support model debugging, validation, investigation triage, false-positive review, audit, and communication of how the persisted synthetic fraud baseline behaves.

## Prohibited Uses

Explanations must not be treated as proof of fraud, criminal conduct, customer intent, or causation. They must not independently justify payment blocking, account closure, customer offboarding, regulatory reporting, sanctions action, law-enforcement referral, or another adverse decision.

## Human Interpretation

Qualified reviewers must interpret explanations alongside source evidence, model limitations, transaction context, data quality, and plausible legitimate behaviour. Reviewers must be able to challenge and document disagreement with model reasons.

## Non-Causal Communication

All coefficient, importance, contribution, and reason-code language must use association-based wording. Feature contributions explain a mathematical model score, not real-world mechanisms or intent.

## Reproducibility And Version Linkage

Every explanation run must link to the persisted pipeline, model metadata, feature list, explainability configuration, and output timestamp. Repeated inputs and configuration should reproduce rankings, contributions, reason codes, and packet selection.

## Configuration Control

Tolerance values, reason counts, minimum contribution, filtering flags, sample size, and communication templates require version control, peer review, testing, approval, and rollback instructions.

## Audit Trail And Feature Lineage

Detailed contributions must retain transformed names, source features, values, coefficients, signed contributions, ranks, categories, and reason inclusion. Source mapping should use the feature dictionary. Identifiers, labels, post-outcome fields, and prohibited inputs must never become explanatory model features.

## Quality Thresholds

Decision and probability reconstruction must remain within configured numerical tolerance. Invalid reasons, excluded-feature violations, missing model inputs, non-finite contributions, or reconstruction failures require a failed run and investigation.

## Incident Handling

An explanation failure should stop publication, preserve affected artifacts, identify impacted model versions and transactions, notify control owners, correct the pipeline or lineage issue, rerun validation, and document resolution.

## False Positives

False-positive explanations should be reviewed for recurring feature patterns, data defects, threshold problems, category instability, and customer friction. A coherent explanation does not validate an incorrect prediction.

## Communication Standards

Use plain, qualified language; distinguish global from local results; report direction and magnitude; disclose synthetic data and limitations; and avoid accusatory, causal, or certainty-based wording.

## Synthetic-Data Disclaimer

All model inputs, labels, identifiers, predictions, and explanations are synthetic. This framework has no regulatory certification or production approval.
