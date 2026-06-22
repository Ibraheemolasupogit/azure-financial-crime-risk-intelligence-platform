# Interview Guide

## 90-Second Explanation

This is a local-first Azure financial-crime platform built entirely on deterministic synthetic banking data. It moves linked customers, accounts, sessions, and transactions through quality gates and prior-only features into a deliberately simple fraud baseline, ten transparent AML controls, customer risk scoring, model explanations, grounded investigation drafts, monitoring, and a Power BI-ready semantic layer. I added an Azure target architecture, Bicep and Azure ML mappings, threat model, governance, MLOps, CI, and runbooks without connecting to cloud services. The value is the end-to-end control story: every score, alert, narrative, and KPI has evidence and limitations. The fraud model is weak and AML alerts are noisy, which I report honestly because the engineering and governance response matters more than inflated synthetic metrics.

## Five-Minute Walkthrough

1. Start with `diagrams/azure_reference_architecture.md` and distinguish local implementation from target Azure services.
2. Show the linked synthetic data and validation report.
3. Explain prior-only velocity/behaviour features and leakage controls.
4. Review fraud metrics/threshold limits and the hybrid AML-plus-ML decision.
5. Trace one customer from alert and prediction through risk components, explanations, investigation evidence, monitoring, and Power BI facts.
6. Close with security, lineage, MLOps approvals, CI, final audit, and known gaps.

## Topic Prompts

- **Architecture:** Event Hubs provides replayable ingestion; ADLS is the system of record; Synapse serves analytics; Azure ML governs model lifecycle; Foundry supports controlled drafting; Purview and Monitor span the platform.
- **Fraud model:** Logistic Regression is inspectable and reproducible, but ROC AUC and average precision are weak. Production work needs better labels, temporal validation, calibration, richer candidates, and cost-sensitive evaluation.
- **AML rules:** Rules encode explicit scenarios and evidence but produce high alert volumes. Tune through governed back-testing and dispositions, never silent suppression.
- **Customer risk:** Five bounded components produce a reconstructable score; it is triage, not proof or an autonomous adverse decision.
- **Explainability:** Native linear contributions reconstruct scores exactly; they explain model mechanics, not causation.
- **GenAI safety:** Local mode is deterministic. Future AI use requires structured evidence, prompt-injection controls, grounding, human approval, and no autonomous SAR filing.
- **Monitoring:** Separate data, drift, fraud, AML, risk, explanation, GenAI, and pipeline controls; no automatic retraining.
- **Power BI:** A privacy-minimised star model, explicit DAX, reconciliation, RLS/OLS design, and governed KPIs.
- **Security:** Entra, managed identity, private endpoints, Key Vault, least privilege, PIM, logging, and environment separation.

## Trade-Offs and Limitations

Local files maximise reproducibility but do not prove cloud scale. Logistic Regression improves transparency but not accuracy. Deterministic GenAI is safe but less flexible. CSV reporting is inspectable but not a deployed semantic model. Illustrative IaC avoids credentials but is not subscription-validated.

## Likely Questions

**Why not deploy it?** The project intentionally separates reproducible implementation from cost- and tenant-dependent deployment; production requires institutional policies, IDs, quotas, networking, and approvals.

**How would you reduce false positives?** Improve labels and segmentation, tune rules against dispositions, calibrate model thresholds on validation periods, combine evidence in case prioritisation, and measure missed-risk trade-offs.

**How do you prevent leakage?** Prior-only temporal windows, chronological splits, feature allowlists, label separation, and tests.

**How would rollback work?** Route a managed endpoint to the previous immutable approved deployment, restore matching feature/config contracts, validate, monitor, and retain evidence.

**Is this compliant?** No compliance claim is made. It demonstrates controls and evidence that require formal legal, regulatory, privacy, security, and model-risk assessment.

**What next?** Subscription-specific threat/design review, Bicep validation, private dev deployment with synthetic data, load/resilience tests, production inference code, data contracts, and formal governance gates.
