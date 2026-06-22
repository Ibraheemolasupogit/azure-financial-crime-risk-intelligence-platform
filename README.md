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

## Ingestion and Validation

Milestone 3 adds a local ingestion and validation layer for the six synthetic banking datasets. The ingestion module reads CSV and JSONL files from `data/raw/` into pandas DataFrames with dataset-specific loader functions and clear missing-file errors.

The validation layer checks required columns, null values in key fields, duplicate primary keys, foreign-key relationships, positive transaction amounts, timestamp parseability, and important categorical value domains.

Validation matters in regulated financial crime systems because downstream fraud models, AML rules, customer risk scores, explainability outputs, analyst workflows, and executive dashboards are only credible when the underlying data is complete, traceable, and relationship-safe.

Run validation locally after generating data:

```bash
python3 scripts/run_data_validation.py
```

Validation produces:

- `reports/data_validation_report.md` for human-readable review
- `outputs/data_validation_results.json` for future dashboard, monitoring, and reporting milestones

Conceptually, this layer maps local raw files to Azure Data Lake Storage zones, transaction-like JSONL records to Azure Event Hubs payloads, validation logic to Azure Stream Analytics or Azure Functions patterns, curated validation outputs to Synapse Analytics and Azure ML readiness checks, data quality evidence to Microsoft Purview, and report artifacts to Power BI workflows. No Azure credentials are required.

## Feature Engineering

Milestone 4 converts validated synthetic inputs into three model-ready analytical tables:

- `data/processed/transaction_features.csv` contains temporal, monetary, prior-only velocity, behavioural, geographic, merchant, channel, device, and session-risk signals.
- `data/processed/account_features.csv` contains account activity, value, failure, cross-border, device, lifecycle, status, and type features.
- `data/processed/customer_features.csv` contains customer behaviour, tenure, account footprint, KYC, sanctions, AML watchlist, and clearly identified historical outcome features.
- `data/processed/feature_dictionary.csv` documents every output column, its category, source, intended use, and leakage risk.

Run the local feature pipeline after data generation and validation:

```bash
python3 scripts/build_features.py
```

The CLI validates all six input datasets before processing and writes quality evidence to `reports/feature_engineering_report.md` and `outputs/feature_engineering_summary.json`.

Leakage controls are deliberate: transaction windows and amount baselines use prior activity only, device novelty is calculated chronologically, and fraud labels are joined only after predictive features are complete. Label columns are excluded from the predictive feature list and classified separately in the feature dictionary. These outputs prepare later fraud modelling, AML monitoring, customer risk scoring, explainability, monitoring, and Power BI milestones without training a model in this milestone.

## Fraud Detection Baseline

Milestone 5 trains a balanced Logistic Regression baseline on the synthetic transaction feature table. Transactions are split chronologically so earlier events form the training set and later events form the test set, reflecting how a real fraud model encounters future activity more closely than a random split.

The sklearn pipeline applies median imputation and scaling to numeric features, most-frequent imputation and one-hot encoding to categorical features, and balanced class weights for the imbalanced fraud target. Identifiers, raw timestamps, current transaction outcomes, label fields, and high-leakage feature-dictionary entries are excluded.

Run the baseline locally:

```bash
python3 scripts/train_fraud_baseline.py
```

The pipeline produces a persisted model, metadata, row-level test predictions, imbalance-aware metrics, threshold analysis, a machine-readable feature list, and ranked Logistic Regression coefficients. The operating threshold is selected by configurable F1 or recall-at-minimum-precision logic; test-set threshold selection is used only for demonstration and would require a separate validation period in production.

Results must be interpreted as synthetic-data workflow evidence, not real detection performance or production readiness. Conceptually, the training and registry workflow maps to Azure Machine Learning, feature and prediction storage to Azure Data Lake Storage, analytical preparation to Synapse Analytics, telemetry to Azure Monitor and Application Insights, lineage to Microsoft Purview, and performance reporting to Power BI. No Azure credentials are required.

## AML Transaction Monitoring

Milestone 6 adds a deterministic and configurable AML rule engine that complements the fraud model with explainable transaction-monitoring controls. Ten scenarios cover high-value activity, structuring, rapid fund movement, synthetic geography conditions, unusual cross-border behaviour, dormant account reactivation, repeated failures, device/session risk, due-diligence exposure, and merchant/channel patterns.

Each alert records the exact rule, configured severity and points, a human-readable reason, and machine-readable evidence containing observed values and thresholds. Alert IDs and timestamps are reproducible for identical data and configuration. Temporal rules use prior history only.

Run the engine locally:

```bash
python3 scripts/run_aml_rules.py
```

Outputs include transaction-level alerts, a customer exposure summary, rule coverage, a machine-readable run summary, and a Markdown report. Customer review priority is an analytical triage aid, not an automated legal decision or composite customer risk score.

Rule monitoring is vulnerable to false positives and requires contextual investigation and threshold tuning. The geography list is synthetic and illustrative and does not classify any country as inherently criminal. Conceptually, the engine maps transaction ingestion to Event Hubs, streaming evaluation to Stream Analytics or Functions, evidence to Data Lake Storage, historical analysis to Synapse, governance to Purview, telemetry to Azure Monitor, and dashboards to Power BI. No Azure services are connected.

## Customer Risk Scoring

Milestone 7 adds a deterministic customer financial-crime risk score for investigation prioritisation. Five independently auditable 0–100 components cover customer and KYC indicators, transaction behaviour, AML alert exposure, fraud-model outputs, and device/session activity.

The total is a transparent weighted sum: 20% KYC, 20% transaction behaviour, 30% AML alerts, 15% fraud model, and 15% device/session risk. Configuration validation requires weights to sum to 1.0, ordered band thresholds, valid mappings, and positive component caps. Detailed component rows reconstruct every total score.

Run locally:

```bash
python3 scripts/score_customer_risk.py
```

Outputs include customer scores, component-level evidence, a portfolio summary, a Markdown report, and a strictly separate retrospective comparison with synthetic labels. Actual fraud labels are rejected by the scoring path and never influence component or total scores.

Risk bands and review priorities are analytical triage aids requiring human review. They do not prove criminal activity or independently justify adverse, legal, sanctions, reporting, or regulatory action. Conceptually, the workflow maps storage to Data Lake Storage, aggregation to Synapse, future learned models to Azure Machine Learning, orchestration to Functions, governance to Purview, telemetry to Azure Monitor, reporting to Power BI, and deployed secrets to Key Vault.

## Fraud Model Explainability

Milestone 8 explains the persisted Logistic Regression baseline using its native linear structure, without retraining the model or adding SHAP. Global outputs rank transformed coefficient associations and aggregate one-hot levels to source features. Local outputs calculate each transaction's transformed value multiplied by its coefficient.

Every local explanation reconstructs the model decision score from the intercept and contributions, then reconstructs probability with the logistic function. Deterministic positive and negative reason codes retain source features, observed values, signed contributions, threshold context, and non-causal caveats.

Run locally:

```bash
python3 scripts/explain_fraud_model.py
```

Outputs include global importance, source-level aggregation, local explanations, detailed contributions, reason codes, reconstruction quality, error-type analysis, a portfolio report, and a limited set of investigator packets. Identifiers, labels, timestamps, and post-outcome fields are prohibited as explanatory model features.

Explanations describe model behaviour and association, not causation, fraud, or criminal conduct. Human review remains mandatory, particularly for the baseline's substantial false-positive population. Conceptually, the layer maps to Azure Machine Learning responsible AI and registry capabilities, Data Lake Storage, Synapse, Azure Monitor, Purview, Power BI, and later Azure AI Foundry assistance.

## GenAI-Assisted Investigations

Milestone 9 adds a safe investigation drafting workflow whose default `deterministic_template` mode requires no LLM, API key, network request, or Azure credential. It assembles minimised structured evidence from customer scores, AML alerts, fraud predictions, and model explanations before generating case summaries, investigator notes, training-only SAR-style drafts, and an executive briefing.

Grounding checks validate numeric claims, transaction and AML references, disclaimers, prohibited language, and word limits. Outputs require human review, use neutral language, and never constitute official submissions or proof of wrongdoing. Disabled Azure OpenAI prompt payloads demonstrate future Azure AI Foundry integration with `network_call_enabled: false`.

Run locally with `python3 scripts/generate_investigation_reports.py`. Conceptually, the workflow maps to Azure AI Foundry, Azure OpenAI, AI Content Safety, Azure Functions, ADLS, Synapse, Key Vault, Purview, Azure Monitor, and Power BI, while remaining fully local in this milestone.

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
python3 scripts/generate_synthetic_data.py
python3 scripts/run_data_validation.py
python3 scripts/build_features.py
python3 scripts/train_fraud_baseline.py
python3 scripts/run_aml_rules.py
python3 scripts/score_customer_risk.py
python3 scripts/explain_fraud_model.py
python3 scripts/generate_investigation_reports.py
python3 -m pytest
python3 -m ruff check .
./scripts/run_all_local.sh
```

## Synthetic Data Notice

All data in this repository is synthetic or sample-only. The project must not use real customers, real accounts, real card data, real banking transactions, or personal data.

Future data generation modules will create fictional entities, accounts, transactions, alerts, and investigation artifacts for demonstration and testing purposes only.

## Portfolio Positioning

This repository is intended to demonstrate applied engineering ability in a domain where trust, auditability, and business context matter. The emphasis is not only on writing code, but on building a coherent platform narrative that technical reviewers can inspect: architecture, testing, documentation, data controls, local reproducibility, and a clear roadmap toward Azure-aligned implementation.

Milestone 1 establishes the foundation. Later milestones will add working components without connecting to live Azure services unless explicitly introduced as optional examples.
