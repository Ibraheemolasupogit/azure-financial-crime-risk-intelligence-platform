# Project Overview

The Azure Financial Crime Risk Intelligence Platform is a local-first portfolio project for simulating financial crime analytics workflows in a banking and FinTech context.

The planned platform will cover synthetic transaction ingestion, validation, feature engineering, fraud detection, AML monitoring, customer risk scoring, explainable ML, investigation workflows, reporting, and GenAI-assisted analysis.

Milestone 1 creates only the scaffold. It does not connect to Azure, use paid services, or include real banking data.

## Synthetic Banking Data Model

Milestone 2 adds a deterministic synthetic data model built around fictional customers, accounts, transactions, device sessions, fraud labels, and AML watchlist alerts.

Customers can hold one or more accounts. Accounts generate transactions. Device sessions represent digital banking activity and are linked to customers, devices, and transaction events. Fraud labels reference transaction IDs for future supervised ML baselines. AML watchlist alerts reference customer IDs for future monitoring, investigation, and reporting workflows.

All entities are synthetic and locally generated. No real banking, customer, card, account, device, or personal data is used.
