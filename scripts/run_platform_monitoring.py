#!/usr/bin/env python
"""Run local platform monitoring and drift reporting."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _domain_status(frame: pd.DataFrame) -> str:
    from src.monitoring.monitor_platform import STATUS_ORDER

    if frame.empty or "status" not in frame:
        return "unavailable"
    return max(frame["status"], key=lambda value: STATUS_ORDER[value])


def main() -> int:
    from src.monitoring.monitor_platform import (
        aggregate_platform_status,
        calculate_aml_rule_monitoring,
        calculate_categorical_feature_drift,
        calculate_customer_risk_monitoring,
        calculate_data_quality_metrics,
        calculate_explainability_monitoring,
        calculate_fraud_model_monitoring,
        calculate_genai_monitoring,
        calculate_numeric_feature_drift,
        check_pipeline_and_artefacts,
        derive_monitoring_periods,
        generate_alerts_from_domains,
        load_monitoring_config,
        write_monitoring_outputs,
    )

    try:
        config = load_monitoring_config()
        transactions = pd.read_csv(config["transaction_features_path"])
        baseline, current, periods = derive_monitoring_periods(transactions)
        predictions = pd.read_csv(config["predictions_path"])
        aml_alerts = pd.read_csv(config["aml_alerts_path"])
        scores = pd.read_csv(config["customer_risk_scores_path"])
        components = pd.read_csv(config["customer_risk_components_path"])
        risk_summary = json.loads(
            Path(config["customer_risk_summary_path"]).read_text(encoding="utf-8")
        )
        explanation_quality = json.loads(
            Path(config["explanation_quality_path"]).read_text(encoding="utf-8")
        )
        genai_quality = json.loads(Path(config["genai_quality_path"]).read_text(encoding="utf-8"))
        prompt_payloads = [
            json.loads(line)
            for line in Path(config["prompt_payloads_path"])
            .read_text(encoding="utf-8")
            .splitlines()
            if line
        ]
        domains = {
            "data_quality": calculate_data_quality_metrics(baseline, current, config),
            "numeric_drift": calculate_numeric_feature_drift(baseline, current, config),
            "categorical_drift": calculate_categorical_feature_drift(baseline, current, config),
            "fraud_model": calculate_fraud_model_monitoring(predictions, config),
            "aml": calculate_aml_rule_monitoring(
                aml_alerts, len(transactions), scores["customer_id"].nunique(), config
            ),
            "customer_risk": calculate_customer_risk_monitoring(
                scores, components, risk_summary, config
            ),
            "explainability": calculate_explainability_monitoring(explanation_quality, config),
            "genai": calculate_genai_monitoring(genai_quality, prompt_payloads, config),
            "pipeline": check_pipeline_and_artefacts(config),
        }
        alerts = generate_alerts_from_domains(domains, config)
        statuses = [status for frame in domains.values() for status in frame.get("status", [])]
        domain_statuses = {name: _domain_status(frame) for name, frame in domains.items()}
        numeric = domains["numeric_drift"].head(int(config["top_drift_feature_count"]))
        categorical = domains["categorical_drift"].head(int(config["top_drift_feature_count"]))
        overall = aggregate_platform_status(domains)
        summary = {
            "run_timestamp": pd.Timestamp.now(tz="UTC").isoformat(),
            "monitoring_version": config["monitoring_version"],
            "baseline_period": periods["baseline"],
            "current_period": periods["current"],
            "domains_monitored": list(domains),
            "healthy_control_count": statuses.count("healthy"),
            "warning_count": statuses.count("warning"),
            "critical_count": statuses.count("critical"),
            "unavailable_count": statuses.count("unavailable"),
            "top_monitoring_alerts": alerts.head(int(config["top_alert_count"])).to_dict(
                orient="records"
            ),
            "top_drifted_features": {
                "numeric": numeric[["feature_name", "psi", "drift_status"]].to_dict(
                    orient="records"
                ),
                "categorical": categorical[
                    ["feature_name", "total_variation_distance", "drift_status"]
                ].to_dict(orient="records"),
            },
            "fraud_model_status": domain_statuses["fraud_model"],
            "AML_control_status": domain_statuses["aml"],
            "risk_scoring_status": domain_statuses["customer_risk"],
            "explainability_status": domain_statuses["explainability"],
            "GenAI_status": domain_statuses["genai"],
            "pipeline_status": domain_statuses["pipeline"],
            "domain_statuses": domain_statuses,
            "overall_platform_status": overall,
            "synthetic_data_statement": "All monitoring inputs and findings are synthetic.",
        }
        paths = write_monitoring_outputs(domains, alerts, summary, config)
    except (FileNotFoundError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        print(f"Platform monitoring failed: {error}")
        return 1

    print("Synthetic platform monitoring complete.")
    print(f"Baseline period: {periods['baseline']}")
    print(f"Current period: {periods['current']}")
    print(f"Domains completed: {', '.join(domains)}")
    print(
        "Controls: "
        f"healthy={summary['healthy_control_count']}, warning={summary['warning_count']}, "
        f"critical={summary['critical_count']}, unavailable={summary['unavailable_count']}"
    )
    print(f"Top numeric drift: {', '.join(numeric['feature_name'].head(3))}")
    print(f"Top categorical drift: {', '.join(categorical['feature_name'].head(3))}")
    for name, status in domain_statuses.items():
        print(f"{name}: {status}")
    print(f"Overall platform status: {overall}")
    print(f"Monitoring alerts: {paths['alerts']}")
    print(f"Monitoring report: {paths['report']}")
    return 1 if overall == "critical" else 0


if __name__ == "__main__":
    raise SystemExit(main())
