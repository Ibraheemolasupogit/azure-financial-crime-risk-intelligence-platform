#!/usr/bin/env python
"""Calculate transparent customer financial-crime risk scores locally."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> int:
    from src.risk_scoring.customer_risk_scoring import (
        calculate_customer_risk_scores,
        generate_portfolio_risk_summary,
        generate_retrospective_evaluation,
        load_aml_customer_summaries,
        load_customer_feature_data,
        load_fraud_prediction_outputs,
        load_risk_config,
        prepare_customer_risk_indicators,
        write_risk_outputs,
        write_risk_report,
    )

    try:
        config = load_risk_config()
        customer_features = load_customer_feature_data(config["customer_features_path"])
        fraud_predictions = load_fraud_prediction_outputs(config["fraud_predictions_path"])
        aml_summary = load_aml_customer_summaries(config["aml_customer_summary_path"])
        transaction_features = pd.read_csv(config["transaction_features_path"])
        customer_profiles = pd.read_csv(config["customer_profiles_path"])
        device_sessions = pd.read_json(config["device_sessions_path"], lines=True)
        fraud_labels = pd.read_csv(config["fraud_labels_path"])

        indicators, missing_statistics = prepare_customer_risk_indicators(
            customer_features,
            customer_profiles,
            transaction_features,
            fraud_predictions,
            aml_summary,
            device_sessions,
            config,
        )
        scores, components = calculate_customer_risk_scores(indicators, config)
        summary = generate_portfolio_risk_summary(
            scores, components, missing_statistics, config
        )
        retrospective = generate_retrospective_evaluation(
            scores, fraud_labels, transaction_features
        )
        paths = write_risk_outputs(scores, components, summary, retrospective, config)
        report_path = Path(config["report_output_path"])
        write_risk_report(summary, config, report_path)
    except (FileNotFoundError, KeyError, TypeError, ValueError) as error:
        print(f"Customer risk scoring failed: {error}")
        return 1

    print("Synthetic customer risk scoring complete.")
    print(f"Customers scored: {summary['customers_scored']}")
    print(f"Average total risk score: {summary['average_total_risk_score']:.4f}")
    print(
        "Risk bands: "
        + ", ".join(
            f"{band}={count}" for band, count in summary["customers_by_risk_band"].items()
        )
    )
    print(
        "Review priorities: "
        + ", ".join(
            f"{priority}={count}"
            for priority, count in summary["customers_by_review_priority"].items()
        )
    )
    top_ids = ", ".join(row["customer_id"] for row in summary["highest_risk_customers"])
    print(f"Highest-risk synthetic customer IDs: {top_ids}")
    print(f"Dominant score component: {summary['dominant_risk_component']}")
    print(f"Risk scores: {paths['scores']}")
    print(f"Component audit: {paths['components']}")
    print(f"Portfolio summary: {paths['summary']}")
    print(f"Retrospective evaluation: {paths['retrospective']}")
    print(f"Report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
