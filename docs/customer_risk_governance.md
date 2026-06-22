# Customer Risk Scoring Governance

## Intended Use

The score is an analytical triage aid for prioritising review of synthetic financial-crime indicators. It supports portfolio analysis, control testing, engineering review, and investigation workflow design.

## Prohibited Uses

The score must not independently trigger account closure, transaction blocking, customer offboarding, sanctions action, regulatory reporting, law-enforcement referral, credit decisions, employment decisions, or any other adverse or legal outcome. It must not be treated as proof of criminal activity.

## Data Minimisation

Scoring outputs contain synthetic customer identifiers and necessary risk indicators only. Names, dates of birth, addresses, and other unnecessary profile details are excluded. Access should follow least-privilege principles in any deployed implementation.

## Human Oversight

A trained reviewer must examine source evidence, context, data quality, and plausible legitimate explanations. Reviewers must be able to challenge, override, and document the analytical priority without pressure to treat the score as a conclusion.

## Explainability And Audit Trail

Every component must expose its raw measures, thresholds, cap, normalised score, configured weight, contribution, reason, and JSON evidence. Weighted contributions must reconstruct the total. Configuration and score versions must accompany outputs.

## Configuration Change Control

Weights, mappings, caps, thresholds, missing-value policy, and reason logic require documented ownership, peer review, testing, approval, effective date, and rollback instructions. Changes should be versioned and compared against the prior configuration before release.

## Threshold Approval

Risk-band and review-priority thresholds require approval from financial-crime operations, model or control risk, compliance, and relevant governance owners. Capacity, false positives, false negatives, customer impact, and escalation service levels should inform approval.

## Monitoring

Monitor score and component distributions, missing data, source freshness, band migration, alert volume, reason frequency, investigation outcomes, override rates, subgroup error rates, latency, failures, and reconstruction integrity. Material drift or pipeline incidents should trigger review.

## Bias And Fairness Review

Review direct and proxy effects across relevant customer groups and geographies. Country, PEP, screening, and device signals require particular care. Geography must not be interpreted as inherent criminality. Investigate disparate error rates and unnecessary customer friction.

## Data-Quality Dependency

The score depends on validated customer features, transaction history, session data, fraud predictions, and AML summaries. Missing or stale inputs can suppress or inflate risk. Critical validation failures must stop scoring rather than silently producing results.

## Incident Handling

Operational procedures should define alerting, containment, impact assessment, output withdrawal, customer remediation where applicable, root-cause analysis, recovery validation, and governance notification.

## Model And Rule Interaction

AML controls, fraud-model outputs, transaction behaviour, and device signals may overlap. Monitoring and change reviews must assess double counting, correlated false positives, model threshold changes, and AML rule revisions before score updates.

## Synthetic-Data Disclaimer

All data and outcomes in this repository are synthetic. This framework has no regulatory approval or production certification and makes no claim of real-world effectiveness.
