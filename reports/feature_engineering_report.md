# Feature Engineering Report

- Run timestamp: `2026-06-22T20:11:26+00:00`
- Overall status: `passed`
- Synthetic data only: `yes`

## Input Row Counts

| Dataset | Rows |
| --- | ---: |
| customers | 50 |
| accounts | 101 |
| transactions | 1468 |
| device_sessions | 200 |
| fraud_labels | 1468 |
| aml_watchlist | 4 |

## Output Feature Tables

| Table | Rows | Columns |
| --- | ---: | ---: |
| transaction_features | 1468 | 45 |
| account_features | 101 | 16 |
| customer_features | 50 | 26 |

## Feature Categories

| Category | Features |
| --- | ---: |
| AML | 1 |
| KYC | 6 |
| account | 12 |
| behavioural | 14 |
| device | 9 |
| geographic | 11 |
| label | 6 |
| monetary | 13 |
| temporal | 8 |
| velocity | 7 |

## Quality Summary

- Missing values: `{"account_features": {}, "customer_features": {}, "transaction_features": {}}`
- Duplicate keys: `{"account_features.account_id": 0, "customer_features.customer_id": 0, "transaction_features.transaction_id": 0}`

## Label Separation

Fraud labels are joined after predictive transaction features are computed and are excluded from the predictive transaction column list.

## Leakage Controls

- Transaction windows are chronological and exclude the current transaction.
- Prior entity averages exclude the current transaction.
- Device novelty is based only on devices seen earlier in transaction order.
- Fraud outcome fields are explicitly classified as label features.
- Customer historical fraud fields are outcome features for retrospective risk analysis, not transaction prediction.
