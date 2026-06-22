# Project Overview

The Azure Financial Crime Risk Intelligence Platform is a local-first portfolio project for simulating financial crime analytics workflows in a banking and FinTech context.

The planned platform will cover synthetic transaction ingestion, validation, feature engineering, fraud detection, AML monitoring, customer risk scoring, explainable ML, investigation workflows, reporting, and GenAI-assisted analysis.

Milestone 1 creates only the scaffold. It does not connect to Azure, use paid services, or include real banking data.

## Synthetic Banking Data Model

Milestone 2 adds a deterministic synthetic data model built around fictional customers, accounts, transactions, device sessions, fraud labels, and AML watchlist alerts.

Customers can hold one or more accounts. Accounts generate transactions. Device sessions represent digital banking activity and are linked to customers, devices, and transaction events. Fraud labels reference transaction IDs for future supervised ML baselines. AML watchlist alerts reference customer IDs for future monitoring, investigation, and reporting workflows.

All entities are synthetic and locally generated. No real banking, customer, card, account, device, or personal data is used.

## Ingestion And Validation

Milestone 3 adds local pandas-based ingestion and validation for the six synthetic datasets. The validation layer checks schemas, key fields, primary keys, relationships, timestamps, transaction amounts, and categorical domains before later feature engineering and ML workflows consume the data.

Validation outputs are written to `reports/data_validation_report.md` and `outputs/data_validation_results.json`. These local artifacts provide a portfolio-friendly simulation of data quality gates that would usually sit between raw landing zones and downstream analytics platforms in a regulated financial crime environment.

## Feature Engineering

Milestone 4 builds transaction, account, and customer feature tables from validated synthetic data. Transaction features use chronological prior-only windows for velocity, amount baselines, geographic behaviour, and device novelty. Account and customer tables provide deterministic descriptive aggregates, KYC and AML signals, and separately identified historical outcomes.

The feature dictionary and quality report make feature purpose, source, leakage risk, missing values, duplicate keys, and label separation reviewable before any model training begins.

## Fraud Detection Baseline

Milestone 5 adds a deterministic sklearn pipeline for synthetic transaction fraud classification. It uses a chronological train/test boundary, balanced Logistic Regression, configurable operating-threshold analysis, imbalance-aware metrics, persisted artifacts, and global coefficient inspection.

The baseline explicitly excludes identifiers, raw timestamps, transaction outcomes, labels, and high-leakage feature-dictionary entries. Its synthetic performance is documented without claims of production readiness.

## AML Transaction Monitoring

Milestone 6 adds ten configurable transaction-monitoring controls with prior-only rolling logic, deterministic alert identifiers, traceable risk points, structured evidence, and customer-level exposure summaries. The engine complements supervised fraud prediction by identifying explainable scenarios that require contextual investigation.

Alerts and customer priorities are triage artifacts only. They do not prove criminal activity, automate legal conclusions, create regulatory submissions, or implement the later composite customer risk-scoring milestone.

## Customer Risk Scoring

Milestone 7 combines five bounded and independently auditable components into a weighted 0–100 customer score. The component audit records raw indicators, thresholds, caps, reasons, configured weights, and contributions so every total can be reconstructed.

Actual fraud labels are prohibited from scoring and used only in a separate retrospective synthetic evaluation. Risk bands and review priorities require contextual human review and must not independently trigger adverse or legal decisions.
