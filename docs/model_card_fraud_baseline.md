# Model Card: Fraud Detection Baseline

## Model Details

- **Name:** Synthetic Transaction Fraud Logistic Regression Baseline
- **Version:** 1.0.0-baseline
- **Model type:** Logistic Regression with balanced class weights
- **Status:** Portfolio baseline; not production-ready

## Intended Use

The model demonstrates deterministic local training, chronological evaluation, imbalance-aware thresholding, artifact persistence, and global coefficient inspection for synthetic transaction fraud classification.

## Out-Of-Scope Uses

It must not be used for real customer decisions, payment blocking, account restriction, regulatory reporting, employee performance assessment, or live fraud investigation. It is not validated for any institution, geography, product, customer population, or protected group.

## Data

Training and evaluation use only locally generated synthetic customer, account, transaction, device-session, and fraud-label data. Earlier transactions form the training data and later transactions form the evaluation data. The target is the synthetic binary `fraud_label`.

Predictive features cover transaction amount, temporal behaviour, velocity, merchant and channel context, geography, devices, and sessions. Identifiers, timestamps, transaction outcomes, labels, label metadata, and high-leakage dictionary fields are excluded.

## Evaluation

| Measure | Result |
| --- | ---: |
| Training rows | 1,101 |
| Test rows | 367 |
| Training fraud prevalence | 4.1780% |
| Test fraud prevalence | 2.7248% |
| Selected threshold | 0.05 |
| Precision | 0.0303 |
| Recall | 1.0000 |
| F1 | 0.0588 |
| ROC AUC | 0.4322 |
| Average precision | 0.0250 |
| True positives / false positives | 10 / 320 |
| True negatives / false negatives | 37 / 0 |

The threshold maximises F1 on the held-out synthetic test set and produces an impractically high false-positive rate. This illustrates the operational cost of prioritising recall when labels contain little learnable signal. A separate validation period would be required for production threshold selection.

## Ethical And Regulatory Considerations

Fraud models can create customer harm through false positives, unequal error rates, opaque decisions, and feedback loops. Any real implementation would require privacy review, lawful processing, fairness assessment, human oversight, explainable decisions, audit trails, model risk management, and documented challenge and approval processes.

## Known Limitations

- Synthetic labels do not reflect realistic fraud mechanisms or investigation outcomes.
- Current metrics should not be compared with institutional fraud models.
- Coefficients describe associations and are not causal.
- The model has not been calibrated or stress-tested.
- Test-set threshold selection is demonstrative and optimistically biased.
- No subgroup, stability, latency, or economic-cost evaluation is included.

## Monitoring Recommendations

Monitor input drift, missing values, category changes, score distributions, fraud prevalence, calibration, precision, recall, false-positive workload, false-negative losses, subgroup error rates, and pipeline health. Alert thresholds should be tied to investigation capacity and risk appetite.

## Retraining Considerations

Retraining should use time-aware validation, delayed label handling, reproducible feature definitions, lineage records, champion-challenger comparison, approval gates, and rollback capability. Trigger review after material drift, control changes, fraud-pattern changes, or sustained performance deterioration.

## Synthetic-Data Disclaimer

All training and evaluation data is synthetic. This model card documents a portfolio engineering artifact and makes no claim of production readiness, regulatory compliance, or real-world fraud detection effectiveness.
