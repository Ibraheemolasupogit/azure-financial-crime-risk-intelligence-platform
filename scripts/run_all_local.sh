#!/usr/bin/env bash
set -euo pipefail

echo "Azure Financial Crime Risk Intelligence Platform"
echo "Current status: Milestone 1 - Repo scaffold"
echo "Azure credentials required: no"
echo "Synthetic data only: yes"
echo

required_paths=(
  "configs/project_config.yaml"
  "src"
  "docs/project_overview.md"
  "tests/test_repo_structure.py"
)

for path in "${required_paths[@]}"; do
  if [[ ! -e "${path}" ]]; then
    echo "Missing required scaffold path: ${path}"
    exit 1
  fi
done

echo "Local scaffold check passed."
echo "No Milestone 2 data generation has been run."
