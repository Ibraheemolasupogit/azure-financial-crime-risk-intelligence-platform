#!/usr/bin/env python
"""Build local feature tables from validated synthetic banking datasets."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

CONFIG_PATH = Path("configs/feature_config.yaml")


def load_config(config_path: Path = CONFIG_PATH) -> dict[str, Any]:
    """Load the local feature configuration."""
    with config_path.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)
    if not isinstance(config, dict):
        raise ValueError(f"Feature configuration must be a mapping: {config_path}")
    return config


def main() -> int:
    from src.features.build_features import (
        build_feature_summary,
        build_final_feature_datasets,
        write_feature_outputs,
        write_feature_quality_outputs,
    )
    from src.ingestion.load_banking_data import load_all_datasets
    from src.validation.validate_banking_data import validate_all_datasets

    try:
        config = load_config()
        datasets = load_all_datasets(Path(config["input_dir"]))
        validation_report = validate_all_datasets(datasets)
        if validation_report["overall_status"] != "passed":
            print("Feature generation stopped: critical input validation checks failed.")
            for check in validation_report["failed_checks"]:
                print(f"- {check['dataset']}.{check['name']}: {check['message']}")
            return 1

        feature_datasets = build_final_feature_datasets(datasets, config)
        output_paths = write_feature_outputs(feature_datasets, Path(config["output_dir"]))
        summary = build_feature_summary(datasets, feature_datasets)
        write_feature_quality_outputs(summary)
    except (FileNotFoundError, KeyError, TypeError, ValueError) as error:
        print(f"Feature generation failed: {error}")
        return 1

    print("Synthetic banking feature engineering complete.")
    for name in ("transaction_features", "account_features", "customer_features"):
        dataframe = feature_datasets[name]
        print(f"- {name}: {len(dataframe)} rows x {len(dataframe.columns)} columns")
        print(f"  output: {output_paths[name]}")
    dictionary = feature_datasets["feature_dictionary"]
    print(f"- feature_dictionary: {len(dictionary)} rows x {len(dictionary.columns)} columns")
    print(f"  output: {output_paths['feature_dictionary']}")
    print(f"Feature quality status: {summary['overall_status']}")
    print("Markdown report: reports/feature_engineering_report.md")
    print("JSON summary: outputs/feature_engineering_summary.json")
    return 0 if summary["overall_status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
