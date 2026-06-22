# Ingestion And Validation

Milestone 3 introduces a local-first ingestion and validation layer for the synthetic banking datasets generated in Milestone 2.

## Local Ingestion Design

The ingestion module reads files from `data/raw/` by default and returns pandas DataFrames. CSV datasets are loaded with `pandas.read_csv`, while transaction and device-session event datasets are loaded from JSONL with `pandas.read_json(..., lines=True)`.

The six supported datasets are:

- `customers.csv`
- `accounts.csv`
- `transactions.jsonl`
- `device_sessions.jsonl`
- `fraud_labels.csv`
- `aml_watchlist.csv`

Each dataset has a dedicated loader, and `load_all_datasets` loads the full data bundle for validation and downstream workflows.

## Validation Checks

The validation layer checks:

- Required columns for every dataset
- Null values in key fields
- Duplicate primary keys
- Foreign-key relationships
- Positive numeric transaction amounts
- Timestamp and date parseability
- Important categorical value domains
- Fraud label references to valid transactions
- AML watchlist references to valid customers

## Relationship Validation

The expected synthetic data relationships are:

```text
customers.customer_id -> accounts.customer_id
customers.customer_id -> device_sessions.customer_id
accounts.account_id -> transactions.account_id
customers.customer_id -> transactions.customer_id
device_sessions.session_id -> transactions.session_id
transactions.transaction_id -> fraud_labels.transaction_id
customers.customer_id -> aml_watchlist.customer_id
```

These checks are intentionally simple and readable so reviewers can inspect the business logic quickly.

## Data Quality Principles

The validation layer is designed around regulated analytics principles:

- Fail early when critical files or relationships are missing.
- Preserve machine-readable evidence for later reporting.
- Keep checks deterministic and locally reproducible.
- Separate ingestion from validation so downstream feature engineering can reuse both layers.
- Avoid secrets, real customer data, and live cloud dependencies.

## Validation Report Outputs

Running `python3 scripts/run_data_validation.py` writes:

- `reports/data_validation_report.md`
- `outputs/data_validation_results.json`

The markdown report is intended for human review. The JSON output is intended for later dashboarding, monitoring, and reporting milestones.

## Azure Mapping

This milestone does not connect to Azure, but the local design maps conceptually to common Azure financial crime architecture patterns:

| Local Component | Azure Concept |
| --- | --- |
| `data/raw/` | Azure Data Lake Storage raw zone |
| `transactions.jsonl` | Azure Event Hubs-style event payloads |
| Validation functions | Azure Stream Analytics / Azure Functions quality gates |
| Loaded DataFrames | Synapse Analytics staging or curated tables |
| Validation JSON | Azure ML data readiness and monitoring artifact |
| Data quality documentation | Microsoft Purview governance evidence |
| Validation reports | Power BI data quality and executive reporting inputs |

## Preparing For Feature Engineering And Model Training

Milestone 3 creates the quality gate needed before Milestone 4 feature engineering and later fraud model training. Downstream components can now assume that core schemas exist, key fields are populated, transaction amounts are valid, timestamps can be parsed, and relationships across customers, accounts, transactions, sessions, labels, and AML alerts are intact.
