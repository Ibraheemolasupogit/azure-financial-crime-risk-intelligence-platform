# Synthetic Data Design

Milestone 2 introduces a deterministic synthetic banking data generator for local development and portfolio demonstration. The datasets are designed to look realistic enough for fraud, AML, risk scoring, explainability, and reporting workflows while remaining entirely fictional.

## Dataset Purpose

| Dataset | Purpose |
| --- | --- |
| `customers.csv` | Synthetic customer profiles with onboarding, KYC, screening, and risk attributes. |
| `accounts.csv` | Synthetic bank accounts linked to customers. |
| `transactions.jsonl` | Synthetic transaction events suitable for fraud and monitoring use cases. |
| `device_sessions.jsonl` | Synthetic digital session activity linked to customers and transaction devices. |
| `fraud_labels.csv` | Synthetic transaction-level fraud labels for supervised ML baselines. |
| `aml_watchlist.csv` | Synthetic customer-level AML alerts and review statuses. |

## Key Entities

The core entity is the customer. Customers can own one or more accounts. Accounts produce transactions. Customers also have digital device sessions, and transactions reference the session and device used. Fraud labels reference transactions. AML watchlist records reference customers.

## Relationships

```text
customers.customer_id -> accounts.customer_id
customers.customer_id -> device_sessions.customer_id
accounts.account_id -> transactions.account_id
customers.customer_id -> transactions.customer_id
device_sessions.session_id -> transactions.session_id
transactions.transaction_id -> fraud_labels.transaction_id
customers.customer_id -> aml_watchlist.customer_id
```

These relationships allow later milestones to test referential integrity, build features at customer/account/transaction level, train baseline fraud models, apply AML scenarios, and produce investigation-ready outputs.

## Privacy Note

All records are synthetic. The generator does not use real customer names, real account numbers, real card data, real device identifiers, real IP addresses, real banking transactions, or personal data.

The generated names, identifiers, events, labels, and alerts are fictional and intended only for local development and demonstration.

## Azure Conceptual Mapping

| Local Synthetic Asset | Azure Concept |
| --- | --- |
| `transactions.jsonl` | Event payloads that could conceptually flow through Azure Event Hubs. |
| `data/raw/` | Local stand-in for Azure Data Lake Storage raw zones. |
| Generated CSV and JSONL files | Sources that could be curated into Azure Synapse Analytics tables. |
| `fraud_labels.csv` | Training labels for future Azure Machine Learning experiments. |
| `aml_watchlist.csv` | Alert and case data for reporting and investigation workflows. |
| Output-ready tabular data | Future Power BI semantic model inputs. |
| Dataset documentation and config | Governance metadata concepts aligned with Microsoft Purview. |

No Azure services are called in Milestone 2.
