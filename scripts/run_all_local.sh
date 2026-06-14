#!/usr/bin/env bash
set -euo pipefail

echo "Azure Financial Crime Risk Intelligence Platform"
echo "Current status: Milestone 2 - Synthetic banking data"
echo "Azure credentials required: no"
echo "Synthetic data only: yes"
echo

PYTHON_BIN="${PYTHON:-python3}"

required_paths=(
  "configs/project_config.yaml"
  "configs/data_generation_config.yaml"
  "src"
  "src/data_generation/generate_banking_data.py"
  "scripts/generate_synthetic_data.py"
  "docs/project_overview.md"
  "tests/test_repo_structure.py"
  "tests/test_data_generation.py"
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
echo "Running tests..."
"${PYTHON_BIN}" -m pytest
echo
echo "Running lint checks..."
"${PYTHON_BIN}" -m ruff check .
echo
echo "Milestone 2 local checks passed."
