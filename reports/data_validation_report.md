# Data Validation Report

- Validation run timestamp: `2026-06-18T16:25:45+00:00`
- Overall validation status: `passed`
- Datasets checked: accounts, aml_watchlist, customers, device_sessions, fraud_labels, transactions

## Row Counts

| Dataset | Rows |
| --- | ---: |
| customers | 50 |
| accounts | 101 |
| transactions | 1468 |
| device_sessions | 200 |
| fraud_labels | 1468 |
| aml_watchlist | 4 |

## Check Summary

- Passed checks: 45
- Failed checks: 0
- Warnings: 0

## Relationship Checks

| Dataset | Check | Status | Message |
| --- | --- | --- | --- |
| accounts | customer_id_references_customers | passed | accounts.customer_id values all exist in customers.customer_id. |
| transactions | account_id_references_accounts | passed | transactions.account_id values all exist in accounts.account_id. |
| transactions | customer_id_references_customers | passed | transactions.customer_id values all exist in customers.customer_id. |
| transactions | session_id_references_device_sessions | passed | transactions.session_id values all exist in device_sessions.session_id. |
| device_sessions | customer_id_references_customers | passed | device_sessions.customer_id values all exist in customers.customer_id. |
| fraud_labels | transaction_id_references_transactions | passed | fraud_labels.transaction_id values all exist in transactions.transaction_id. |
| aml_watchlist | customer_id_references_customers | passed | aml_watchlist.customer_id values all exist in customers.customer_id. |

## Failed Checks

No failed checks.

## Warnings

No warnings.
