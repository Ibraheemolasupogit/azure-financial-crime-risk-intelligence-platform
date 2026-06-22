#!/usr/bin/env bash
set -euo pipefail

echo "Azure Financial Crime Risk Intelligence Platform"
echo "Current status: Milestone 12 - Azure architecture and portfolio assurance"
echo "Azure credentials required: no"
echo "Synthetic data only: yes"
echo

PYTHON_BIN="${PYTHON:-python3}"

required_paths=(
  "configs/project_config.yaml"
  "configs/data_generation_config.yaml"
  "configs/feature_config.yaml"
  "configs/fraud_model_config.yaml"
  "configs/aml_rules_config.yaml"
  "configs/customer_risk_config.yaml"
  "configs/explainability_config.yaml"
  "configs/genai_investigation_config.yaml"
  "configs/monitoring_config.yaml"
  "configs/reporting_config.yaml"
  "src"
  "src/data_generation/generate_banking_data.py"
  "src/ingestion/load_banking_data.py"
  "src/validation/validate_banking_data.py"
  "src/features/build_features.py"
  "src/models/train_fraud_baseline.py"
  "src/aml_rules/aml_rule_engine.py"
  "src/risk_scoring/customer_risk_scoring.py"
  "src/explainability/explain_fraud_model.py"
  "src/genai/investigation_assistant.py"
  "src/genai/prompt_templates.py"
  "src/monitoring/monitor_platform.py"
  "src/reporting/build_powerbi_outputs.py"
  "scripts/generate_synthetic_data.py"
  "scripts/run_data_validation.py"
  "scripts/build_features.py"
  "scripts/train_fraud_baseline.py"
  "scripts/run_aml_rules.py"
  "scripts/score_customer_risk.py"
  "scripts/explain_fraud_model.py"
  "scripts/generate_investigation_reports.py"
  "scripts/run_platform_monitoring.py"
  "scripts/build_powerbi_outputs.py"
  "scripts/validate_infrastructure.py"
  "scripts/run_final_audit.py"
  "diagrams/azure_reference_architecture.mmd"
  "infra/main.bicep"
  "azureml/README.md"
  "docs/security_architecture.md"
  "docs/threat_model.md"
  "docs/portfolio_evidence.md"
  "docs/project_overview.md"
  "tests/test_repo_structure.py"
  "tests/test_data_generation.py"
  "tests/test_ingestion.py"
  "tests/test_validation.py"
  "tests/test_feature_engineering.py"
  "tests/test_fraud_baseline.py"
  "tests/test_aml_rule_engine.py"
  "tests/test_customer_risk_scoring.py"
  "tests/test_model_explainability.py"
  "tests/test_genai_investigation_assistant.py"
  "tests/test_platform_monitoring.py"
  "tests/test_powerbi_reporting.py"
  "tests/test_final_portfolio.py"
)

for path in "${required_paths[@]}"; do
  if [[ ! -e "${path}" ]]; then
    echo "Missing required scaffold path: ${path}"
    exit 1
  fi
done

echo "Local scaffold check passed."
echo
echo "Generating synthetic banking data..."
"${PYTHON_BIN}" scripts/generate_synthetic_data.py
echo
echo "Running data ingestion and validation..."
"${PYTHON_BIN}" scripts/run_data_validation.py
echo
echo "Building model-ready feature tables..."
"${PYTHON_BIN}" scripts/build_features.py
echo
echo "Training fraud detection baseline..."
"${PYTHON_BIN}" scripts/train_fraud_baseline.py
echo
echo "Running AML transaction-monitoring rules..."
"${PYTHON_BIN}" scripts/run_aml_rules.py
echo
echo "Scoring customer financial-crime risk..."
"${PYTHON_BIN}" scripts/score_customer_risk.py
echo
echo "Generating fraud model explanations..."
"${PYTHON_BIN}" scripts/explain_fraud_model.py
echo
echo "Generating grounded investigation drafts..."
"${PYTHON_BIN}" scripts/generate_investigation_reports.py
echo
echo "Running platform monitoring and drift reporting..."
"${PYTHON_BIN}" scripts/run_platform_monitoring.py
echo
echo "Building Power BI-ready analytical outputs..."
"${PYTHON_BIN}" scripts/build_powerbi_outputs.py
echo
echo "Validating illustrative infrastructure scaffold..."
"${PYTHON_BIN}" scripts/validate_infrastructure.py
echo
echo "Running final portfolio audit..."
"${PYTHON_BIN}" scripts/run_final_audit.py
echo
echo "Running tests..."
"${PYTHON_BIN}" -m pytest
echo
echo "Running lint checks..."
"${PYTHON_BIN}" -m ruff check .
echo
echo "Final CI checks passed. All 12 milestones are represented."
