# Azure Financial Crime Risk Intelligence Platform

Production-style scaffold for a local-first Financial Crime and Risk Intelligence Platform inspired by Azure banking and fintech architectures.

## Big-Picture Explanation

This repository is designed as a flagship portfolio project for financial crime analytics, fraud detection, AML monitoring, customer risk scoring, explainable machine learning, investigation workflows, executive reporting, and GenAI-assisted analysis.

The platform will simulate how a regulated financial institution could move from raw transaction events to risk intelligence: ingesting synthetic banking activity, validating data quality, generating model-ready features, applying fraud and AML controls, scoring customers and entities, explaining model outputs, and producing investigation and reporting artifacts.

Milestone 1 is intentionally limited to the repository scaffold. No Azure resources are provisioned, no paid services are used, and no real financial or personal data is included.

## Why This Repo Matters

Financial crime teams need systems that are technically credible, auditable, explainable, and operationally useful. This project demonstrates how modern data engineering, machine learning engineering, analytics engineering, and cloud architecture practices can be combined for risk and compliance use cases.

It is built to show practical judgment across:

- Synthetic transaction data design
- Fraud analytics and anomaly detection
- AML scenario monitoring
- Customer and entity risk scoring
- Explainable ML for regulated environments
- Investigation support workflows
- Executive-ready reporting outputs
- Azure-aligned architecture without requiring live cloud services

## Target Roles And Companies

This repository is positioned for review by:

- Banks and digital banks
- FinTech companies
- Payments companies
- Fraud analytics teams
- AML and financial crime teams
- Risk analytics and credit risk teams
- ML engineering and MLOps teams
- Data engineering and analytics engineering teams
- Cloud solution architecture teams
- Technical recruiters, hiring managers, and interview panels

Relevant roles include Financial Crime Analytics Engineer, Fraud Data Scientist, AML Analytics Specialist, Risk ML Engineer, Azure Data Engineer, MLOps Engineer, Analytics Engineer, and FinTech Cloud Engineer.

## Core Use Case

The planned end-to-end use case is a synthetic financial institution monitoring retail banking and payments activity. The platform will ingest synthetic transactions, detect suspicious activity, generate customer risk scores, explain model decisions, support investigation workflows, and produce reporting outputs suitable for operational and executive review.

## Azure Service Mapping

| Capability | Azure Service Mapping |
| --- | --- |
| Transaction ingestion | Azure Event Hubs |
| Batch data lake | Azure Data Lake Storage |
| Stream processing | Azure Stream Analytics / Azure Functions |
| Data warehouse | Azure Synapse Analytics |
| ML training | Azure Machine Learning |
| Model serving | Azure ML Managed Endpoint |
| GenAI investigation | Azure AI Foundry / Azure OpenAI |
| Secrets | Azure Key Vault |
| Monitoring | Azure Monitor / Application Insights |
| Dashboard | Power BI |
| Governance | Microsoft Purview |

## MVP Scope

The MVP will be implemented incrementally and remain runnable locally. The first complete version will include synthetic data generation, validation checks, feature engineering, a baseline fraud model, AML rule scenarios, customer risk scoring, model explainability outputs, local reports, and Power BI-ready artifacts.

Milestone 1 delivers the production-style scaffold and documentation foundation. Milestone 2 adds deterministic synthetic banking data generation.

## Synthetic Banking Data

Milestone 2 adds a local synthetic banking data generator that creates six linked datasets:

| Dataset | Description |
| --- | --- |
| `customers.csv` | Fictional customer profiles with onboarding, KYC, screening, segment, and risk attributes. |
| `accounts.csv` | Fictional accounts linked to synthetic customers. |
| `transactions.jsonl` | Synthetic transaction events with channel, merchant, amount, device, and session context. |
| `device_sessions.jsonl` | Synthetic digital banking session records linked to customers and devices. |
| `fraud_labels.csv` | Synthetic transaction-level labels for future fraud model development. |
| `aml_watchlist.csv` | Synthetic customer-level AML alerts for monitoring and investigation workflows. |

Synthetic data is used so the project can demonstrate banking and financial crime analytics patterns without exposing real customers, real accounts, real card data, real devices, personal data, or confidential financial institution records.

Run the generator locally:

```bash
python3 scripts/generate_synthetic_data.py
```

Generated outputs are written to `data/raw/`. Small representative samples are stored in `data/samples/` for quick inspection and documentation.

These datasets support later milestones by providing linked entities for fraud detection, AML rules, customer risk scoring, explainability, monitoring, reporting, and Power BI-ready outputs. The data model also gives future Azure-aligned architecture work concrete local artifacts to map conceptually to Event Hubs, Data Lake Storage, Synapse Analytics, Azure Machine Learning, Power BI, and Microsoft Purview.

## Planned ML Use Cases

- Transaction fraud classification
- Suspicious activity anomaly detection
- Customer risk scoring
- Entity behavior segmentation
- Rule-plus-model alert prioritization
- Model drift and data quality monitoring
- Explainability for fraud and risk decisions

## Planned GenAI Use Cases

- Investigation case summarization
- Alert narrative drafting
- Suspicious activity pattern explanation
- Analyst question answering over synthetic case artifacts
- Executive risk briefing generation
- Control gap analysis using synthetic scenarios

GenAI features will be designed as local-safe prototypes first. Any Azure AI Foundry or Azure OpenAI integration will remain optional and documented separately in later milestones.

## Repository Structure

```text
configs/                  Project configuration files
data/                     Synthetic data storage
  raw/                    Raw generated sample inputs
  processed/              Cleaned and feature-ready outputs
  samples/                Small sample datasets for tests and demos
src/                      Importable Python source modules
  data_generation/        Synthetic customer and transaction generation
  ingestion/              Local ingestion simulation
  validation/             Data quality checks
  features/               Feature engineering logic
  models/                 Baseline ML model code
  risk_scoring/           Customer and entity risk scoring
  aml_rules/              AML scenario rule engine
  explainability/         Explainability and reason-code outputs
  genai/                  GenAI-assisted investigation prototypes
  reporting/              Report and export generation
  monitoring/             Metrics, drift, and operational checks
docs/                     Project documentation
diagrams/                 Architecture and design placeholders
outputs/
  reports/                Generated local reports
dashboard/                Dashboard assets and future app files
tests/                    Automated tests
scripts/                  Local utility scripts
.github/workflows/        CI workflows
```

## Milestone Roadmap

| Milestone | Scope |
| --- | --- |
| Milestone 1 | Repo scaffold |
| Milestone 2 | Synthetic banking data |
| Milestone 3 | Ingestion and validation |
| Milestone 4 | Feature engineering |
| Milestone 5 | Fraud detection baseline model |
| Milestone 6 | AML rule engine |
| Milestone 7 | Customer risk scoring |
| Milestone 8 | Model explainability |
| Milestone 9 | GenAI investigation assistant |
| Milestone 10 | Monitoring and drift reporting |
| Milestone 11 | Power BI-ready outputs |
| Milestone 12 | Azure architecture and portfolio polish |

## Local Setup

This project currently requires no Azure credentials and no paid services.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/generate_synthetic_data.py
pytest
ruff check .
./scripts/run_all_local.sh
```

## Synthetic Data Notice

All data in this repository is synthetic or sample-only. The project must not use real customers, real accounts, real card data, real banking transactions, or personal data.

Future data generation modules will create fictional entities, accounts, transactions, alerts, and investigation artifacts for demonstration and testing purposes only.

## Portfolio Positioning

This repository is intended to demonstrate applied engineering ability in a domain where trust, auditability, and business context matter. The emphasis is not only on writing code, but on building a coherent platform narrative that technical reviewers can inspect: architecture, testing, documentation, data controls, local reproducibility, and a clear roadmap toward Azure-aligned implementation.

Milestone 1 establishes the foundation. Later milestones will add working components without connecting to live Azure services unless explicitly introduced as optional examples.
