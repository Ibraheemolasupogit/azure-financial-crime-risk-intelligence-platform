# 10–15 Minute Demo Guide

## Preparation

Create the local environment and run `./scripts/run_all_local.sh`. No Azure credentials or network access are needed after dependencies are installed.

## Demo Sequence

1. **Repository overview (1 minute):** open `README.md`; state synthetic-only, local-first, and no live cloud deployment.
2. **Synthetic data (1 minute):** run `python3 scripts/generate_synthetic_data.py`; inspect `data/samples/transactions_sample.jsonl` and linked IDs.
3. **Validation (1 minute):** run `python3 scripts/run_data_validation.py`; open `reports/data_validation_report.md`.
4. **Features (1 minute):** run `python3 scripts/build_features.py`; inspect `data/processed/feature_dictionary.csv`; explain prior-only windows.
5. **Fraud baseline (1 minute):** run `python3 scripts/train_fraud_baseline.py`; open `reports/fraud_baseline_model_report.md`; call out weak performance honestly.
6. **AML rules (1 minute):** run `python3 scripts/run_aml_rules.py`; inspect `docs/aml_controls_matrix.md` and `outputs/aml_rule_summary.csv`; discuss false positives.
7. **Customer risk (1 minute):** run `python3 scripts/score_customer_risk.py`; trace `outputs/customer_risk_components.csv` to total score.
8. **Explanations (1 minute):** run `python3 scripts/explain_fraud_model.py`; open an investigator explanation and show probability reconstruction.
9. **Investigation reports (1 minute):** run `python3 scripts/generate_investigation_reports.py`; open a case report and grounding JSON; stress human review.
10. **Monitoring (1 minute):** run `python3 scripts/run_platform_monitoring.py`; open `reports/platform_monitoring_report.md`.
11. **Power BI-ready outputs (1 minute):** run `python3 scripts/build_powerbi_outputs.py`; show semantic spec, DAX, and executive KPIs.
12. **Azure architecture (2 minutes):** open `diagrams/azure_reference_architecture.md`, `infra/README.md`, security architecture, and MLOps lifecycle; distinguish mappings from deployed controls.

Close with `python3 scripts/run_final_audit.py`, test count, limitations, and the production path. Avoid presenting synthetic metrics as bank performance or the reference templates as deployed infrastructure.
