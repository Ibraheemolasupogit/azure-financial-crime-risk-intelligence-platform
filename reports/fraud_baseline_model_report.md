# Fraud Detection Baseline Model Report

- Model: `LogisticRegression` with balanced class weights
- Training rows: 1101
- Test rows: 367
- Training fraud prevalence: 4.1780%
- Test fraud prevalence: 2.7248%
- Chronological test boundary: `2025-10-09T02:46:37`
- Predictive feature count: 34
- Selected threshold: 0.05

## Imbalance-Aware Metrics

| Metric | Value |
| --- | ---: |
| Precision | 0.0303 |
| Recall | 1.0000 |
| F1 | 0.0588 |
| ROC AUC | 0.4322 |
| Average precision | 0.0250 |
| Accuracy (secondary) | 0.1281 |
| False-positive rate | 0.8964 |
| False-negative rate | 0.0000 |

## Confusion Matrix

- True positives: 10
- False positives: 320
- True negatives: 37
- False negatives: 0

## Largest Positive Coefficients

| Feature | Coefficient |
| --- | ---: |
| categorical__ip_country_IE | 1.727286 |
| categorical__ip_country_ES | 1.400823 |
| numeric__amount_vs_customer_average | 1.096502 |
| categorical__customer_country_DE | 1.031800 |
| numeric__transaction_count_customer_24h | 1.021768 |
| categorical__merchant_country_GB | 0.789485 |
| categorical__merchant_country_BR | 0.780265 |
| numeric__is_cross_border | 0.751535 |
| categorical__merchant_country_CA | 0.719043 |
| numeric__distinct_countries_customer_7d | 0.634069 |

## Largest Negative Coefficients

| Feature | Coefficient |
| --- | ---: |
| numeric__amount_vs_account_average | -2.295765 |
| categorical__ip_country_FR | -1.648696 |
| categorical__merchant_country_SG | -1.483781 |
| numeric__transaction_velocity_score | -1.279600 |
| categorical__ip_country_ZA | -1.117885 |
| numeric__transaction_amount_customer_24h | -1.049156 |
| categorical__merchant_country_DE | -0.886899 |
| categorical__customer_country_ES | -0.800456 |
| categorical__currency_CAD | -0.800077 |
| categorical__customer_country_CA | -0.800077 |

## Threshold And Leakage Notes

The operating threshold was selected on held-out test data for demonstration. A production workflow should use a separate validation set or time-aware cross-validation.

Identifiers, raw timestamps, labels, transaction outcomes, and feature-dictionary fields marked as labels or high leakage risk were excluded before fitting.

All performance results are based on synthetic data and do not establish production readiness.
