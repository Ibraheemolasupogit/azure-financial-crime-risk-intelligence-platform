#!/usr/bin/env python
"""Train and evaluate the local synthetic fraud baseline model."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

CONFIG_PATH = Path("configs/fraud_model_config.yaml")


def load_config(config_path: Path = CONFIG_PATH) -> dict[str, Any]:
    """Load fraud baseline configuration."""
    with config_path.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)
    if not isinstance(config, dict):
        raise ValueError(f"Fraud model configuration must be a mapping: {config_path}")
    return config


def main() -> int:
    from src.models.train_fraud_baseline import (
        load_feature_dictionary,
        load_transaction_features,
        save_model_artifacts,
        train_and_evaluate,
        write_model_outputs,
        write_model_report,
    )

    try:
        config = load_config()
        features = load_transaction_features(config["input_path"])
        feature_dictionary = load_feature_dictionary(config["feature_dictionary_path"])
        result = train_and_evaluate(features, feature_dictionary, config)
        model_paths = save_model_artifacts(
            result["pipeline"], result["metadata"], config["model_output_dir"]
        )
        write_model_outputs(
            result["predictions"],
            result["threshold_analysis"],
            result["feature_columns"],
            result["metrics"],
            result["coefficients"],
            config,
        )
        report_path = Path(config["report_output_dir"]) / "fraud_baseline_model_report.md"
        write_model_report(
            result["metrics"],
            result["coefficients"],
            len(result["feature_columns"]),
            result["split_boundary"],
            report_path,
            int(config["top_feature_count"]),
        )
    except (FileNotFoundError, KeyError, TypeError, ValueError) as error:
        print(f"Fraud baseline training failed: {error}")
        return 1

    metrics = result["metrics"]
    print("Synthetic fraud baseline training complete.")
    print(f"Training rows: {metrics['training_row_count']}")
    print(f"Test rows: {metrics['test_row_count']}")
    print(f"Training fraud prevalence: {metrics['training_fraud_rate']:.4%}")
    print(f"Test fraud prevalence: {metrics['test_fraud_rate']:.4%}")
    print(f"Selected threshold: {metrics['selected_threshold']:.2f}")
    print(f"Precision: {metrics['precision']:.4f}")
    print(f"Recall: {metrics['recall']:.4f}")
    print(f"F1: {metrics['f1_score']:.4f}")
    print(f"ROC AUC: {metrics['roc_auc']:.4f}")
    print(f"Average precision: {metrics['average_precision']:.4f}")
    print(f"Model: {model_paths['model']}")
    print(f"Report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
