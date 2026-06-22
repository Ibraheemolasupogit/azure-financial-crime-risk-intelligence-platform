#!/usr/bin/env python
"""Run local ingestion and validation for synthetic banking datasets."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> int:
    from src.ingestion.load_banking_data import load_all_datasets
    from src.validation.validate_banking_data import validate_all_datasets, write_validation_outputs

    datasets = load_all_datasets()
    report = validate_all_datasets(datasets)
    write_validation_outputs(report)

    print("Synthetic banking data validation complete.")
    print(f"Overall status: {report['overall_status']}")
    print(f"Datasets checked: {', '.join(report['datasets_checked'])}")
    print(f"Passed checks: {len(report['passed_checks'])}")
    print(f"Failed checks: {len(report['failed_checks'])}")
    print("Markdown report: reports/data_validation_report.md")
    print("JSON results: outputs/data_validation_results.json")

    return 0 if report["overall_status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
