#!/usr/bin/env bash
set -euo pipefail

echo "Azure Financial Crime Risk Intelligence Platform"
echo "Current status: Milestone 4 - Feature engineering"
echo "Azure credentials required: no"
echo "Synthetic data only: yes"
echo

PYTHON_BIN="${PYTHON:-python3}"

required_paths=(
  "configs/project_config.yaml"
  "configs/data_generation_config.yaml"
  "configs/feature_config.yaml"
  "src"
  "src/data_generation/generate_banking_data.py"
  "src/ingestion/load_banking_data.py"
  "src/validation/validate_banking_data.py"
  "src/features/build_features.py"
  "scripts/generate_synthetic_data.py"
  "scripts/run_data_validation.py"
  "scripts/build_features.py"
  "docs/project_overview.md"
  "tests/test_repo_structure.py"
  "tests/test_data_generation.py"
  "tests/test_ingestion.py"
  "tests/test_validation.py"
  "tests/test_feature_engineering.py"
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
echo "Running tests..."
"${PYTHON_BIN}" -m pytest
echo
echo "Running lint checks..."
"${PYTHON_BIN}" -m ruff check .
echo
echo "Milestone 4 local checks passed."
