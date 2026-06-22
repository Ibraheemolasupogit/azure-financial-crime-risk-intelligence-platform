#!/usr/bin/env python
"""Run deterministic AML monitoring rules on validated synthetic data."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> int:
    from src.aml_rules.aml_rule_engine import (
        aggregate_alerts_by_customer,
        build_rule_summary,
        evaluate_all_enabled_rules,
        generate_aml_summary_metrics,
        load_aml_config,
        prepare_aml_data,
        write_aml_outputs,
        write_aml_report,
    )
    from src.ingestion.load_banking_data import load_all_datasets
    from src.validation.validate_banking_data import validate_all_datasets

    try:
        config = load_aml_config()
        datasets = load_all_datasets(Path(config["input_dir"]))
        validation = validate_all_datasets(datasets)
        if validation["overall_status"] != "passed":
            print("AML rule evaluation stopped: critical input validation checks failed.")
            for check in validation["failed_checks"]:
                print(f"- {check['dataset']}.{check['name']}: {check['message']}")
            return 1

        feature_path = Path(config["transaction_features_path"])
        if not feature_path.exists():
            raise FileNotFoundError(
                f"Transaction feature file not found: {feature_path}. "
                "Run `python3 scripts/build_features.py` first."
            )
        transaction_features = pd.read_csv(feature_path)
        prepared = prepare_aml_data(datasets, transaction_features)
        alerts = evaluate_all_enabled_rules(prepared, config)
        customer_summary = aggregate_alerts_by_customer(alerts, config)
        rule_summary = build_rule_summary(alerts, len(prepared), config)
        run_summary = generate_aml_summary_metrics(
            prepared, alerts, customer_summary, config
        )
        output_paths = write_aml_outputs(
            alerts, customer_summary, rule_summary, run_summary, config
        )
        report_path = Path(config["report_output_path"])
        write_aml_report(run_summary, rule_summary, report_path)
    except (FileNotFoundError, KeyError, TypeError, ValueError) as error:
        print(f"AML rule evaluation failed: {error}")
        return 1

    print("Synthetic AML rule evaluation complete.")
    print(f"Transactions evaluated: {len(prepared)}")
    print(f"Enabled rules: {len(config['enabled_rules'])}")
    print(f"Total alerts: {len(alerts)}")
    print(f"Alerted transactions: {run_summary['alerted_transactions']}")
    print(f"Affected customers: {run_summary['affected_customers']}")
    severity_text = ", ".join(
        f"{severity}={count}"
        for severity, count in run_summary["alerts_by_severity"].items()
    )
    print(f"Alerts by severity: {severity_text or 'none'}")
    top_rules = rule_summary.nlargest(3, "alert_count")
    print(
        "Top triggered rules: "
        + ", ".join(f"{row.rule_id}={row.alert_count}" for row in top_rules.itertuples())
    )
    print(f"Alerts: {output_paths['alerts']}")
    print(f"Customer summary: {output_paths['customer_summary']}")
    print(f"Rule summary: {output_paths['rule_summary']}")
    print(f"Run summary: {output_paths['run_summary']}")
    print(f"Report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
