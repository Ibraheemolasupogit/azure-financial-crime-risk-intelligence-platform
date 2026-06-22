# Feature Engineering

Milestone 4 transforms the six validated synthetic banking datasets into deterministic transaction-level, account-level, and customer-level feature tables. Processing remains local, uses the existing ingestion and validation layers, and does not train or serve a model.

## Feature Tables

| Table | Grain | Primary purpose |
| --- | --- | --- |
| `transaction_features.csv` | One row per transaction | Fraud detection, anomaly detection, explainability, and transaction monitoring inputs |
| `account_features.csv` | One row per account | Account behaviour, exposure, and lifecycle analysis |
| `customer_features.csv` | One row per customer | Customer risk scoring, AML monitoring, and portfolio reporting |
| `feature_dictionary.csv` | One row per output column | Feature meaning, source, category, intended use, and leakage classification |

## Feature Categories

The feature dictionary classifies fields as temporal, monetary, behavioural, velocity, geographic, device, account, KYC, AML, or label. This makes the boundary between predictive signals, static customer-risk attributes, and historical outcomes explicit.

Temporal and monetary features include transaction hour, weekday, weekend/night flags, log amount, and amount relative to prior account and customer averages. The configured reference timestamp makes account and customer tenure reproducible.

Behavioural and velocity features use chronological transaction order. Customer and account counts and amounts use a configurable 24-hour window; country, merchant-category, and cross-border history use a configurable seven-day window. The current transaction is excluded from these rolling values. A rapid-transaction flag compares each event with the customer's immediately preceding event.

Device and session signals include first-seen device activity, risky session indicators, and country mismatches between the synthetic customer, session IP, and merchant. Geographic and merchant signals identify cross-border activity and configured higher-risk countries, channels, and merchant categories.

## KYC, AML, And Outcomes

The customer table contains encoded PEP, KYC, and sanctions-screening attributes plus an AML watchlist flag. These fields are kept conceptually distinct from behavioural aggregates.

Fraud labels are not read while predictive transaction features are calculated. They are joined only after the predictive table is complete and are identified as label fields in the feature dictionary. Customer `historical_fraud_count` and `historical_fraud_rate` fields are retrospective outcome features for customer-risk analysis and reporting; they are not eligible inputs for transaction-level fraud prediction.

## Leakage Prevention And Determinism

- Rolling transaction windows contain prior events only.
- Entity amount averages exclude the current transaction.
- Device novelty uses devices observed earlier in chronological transaction order.
- Supervised fraud outcomes are joined after predictive feature computation.
- The feature dictionary marks outcome fields with high leakage risk and outcome-only intended use.
- Stable sorting and a fixed reference timestamp make repeated runs reproducible.

## Quality Outputs

The pipeline writes `reports/feature_engineering_report.md` and `outputs/feature_engineering_summary.json`. They record input and output row counts, feature counts, missing values, duplicate keys, feature categories, leakage controls, and overall status.

Run the complete feature stage locally:

```bash
python3 scripts/build_features.py
```

## Azure Conceptual Mapping

| Local capability | Azure-aligned concept |
| --- | --- |
| Transaction JSONL events | Azure Event Hubs transaction events |
| Raw and processed local files | Azure Data Lake Storage raw and curated zones |
| Prior-only velocity logic | Azure Stream Analytics or Azure Functions streaming features |
| Analytical joins and aggregates | Azure Synapse Analytics feature preparation |
| Model-ready feature tables | Azure Machine Learning training datasets and pipelines |
| Feature dictionary and source metadata | Microsoft Purview lineage, classification, and governance |
| Customer and account aggregates | Power BI operational and portfolio analytics |

These mappings are architectural only. Milestone 4 uses no Azure credentials, paid services, deployment resources, or real financial data.
