import json
from copy import deepcopy
from pathlib import Path

import numpy as np
import pandas as pd
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
    categorical_total_variation,
    check_pipeline_and_artefacts,
    create_monitoring_alert,
    derive_monitoring_periods,
    load_monitoring_config,
    population_stability_index,
    write_monitoring_outputs,
)


def _config() -> dict:
    return deepcopy(load_monitoring_config())


def _transactions() -> pd.DataFrame:
    count = 20
    index = np.arange(count)
    return pd.DataFrame(
        {
            "transaction_id": [f"T{i}" for i in index],
            "transaction_timestamp": pd.date_range("2025-01-01", periods=count, freq="D"),
            "amount": 10 + index,
            "log_transaction_amount": np.log1p(10 + index),
            "amount_vs_account_average": 1 + index / 100,
            "amount_vs_customer_average": 1 + index / 100,
            "transaction_count_customer_24h": index % 3,
            "transaction_amount_customer_24h": index * 2,
            "transaction_velocity_score": index / 10,
            "cross_border_transaction_count_7d": index % 4,
            "risky_session_flag": index % 2,
            "country_mismatch_flag": index % 2,
            "channel": np.where(index < 10, "Branch", "ATM"),
            "transaction_type": "Card Purchase",
            "merchant_category": "Grocery",
            "merchant_country": "GB",
            "transaction_status": "Approved",
            "session_risk_signal": "Low",
        }
    )


def test_config_and_periods_are_deterministic() -> None:
    assert load_monitoring_config()["monitoring_version"] == "1.0.0"
    first = derive_monitoring_periods(_transactions())
    second = derive_monitoring_periods(_transactions())
    assert first[2] == second[2]
    assert len(first[0]) == len(first[1]) == 10


def test_data_quality_row_missing_and_duplicate_metrics() -> None:
    config = _config()
    baseline, current, _ = derive_monitoring_periods(_transactions())
    current = pd.concat([current, current.iloc[[0]]], ignore_index=True)
    current.loc[0, "channel"] = None
    metrics = calculate_data_quality_metrics(baseline, current, config)
    assert metrics.query("metric_name == 'row_count_change'").iloc[0].current_value == 0.1
    assert metrics.query("metric_name == 'maximum_missing_value_rate'").iloc[0].current_value > 0
    assert metrics.query("metric_name == 'duplicate_primary_keys'").iloc[0].current_value == 1


def test_numeric_psi_is_finite_and_constant_safe() -> None:
    assert population_stability_index(pd.Series([1, 1]), pd.Series([1, 1])) == 0
    psi = population_stability_index(pd.Series(range(20)), pd.Series(range(10, 30)))
    assert np.isfinite(psi) and psi >= 0
    baseline, current, _ = derive_monitoring_periods(_transactions())
    drift = calculate_numeric_feature_drift(baseline, current, _config())
    assert drift["psi"].map(np.isfinite).all()


def test_categorical_drift_and_new_categories() -> None:
    distance, new_count, _, changed = categorical_total_variation(
        pd.Series(["A", "A", "B"]), pd.Series(["C", "C", "B"])
    )
    assert 0 <= distance <= 1
    assert new_count == 1 and changed
    baseline, current, _ = derive_monitoring_periods(_transactions())
    drift = calculate_categorical_feature_drift(baseline, current, _config())
    assert "total_variation_distance" in drift


def test_fraud_metrics_and_empty_positive_periods_are_safe() -> None:
    frame = pd.DataFrame(
        {
            "transaction_id": [f"T{i}" for i in range(8)],
            "transaction_timestamp": pd.date_range("2025-01-01", periods=8),
            "actual_fraud_label": [0, 1, 0, 1, 0, 0, 0, 0],
            "predicted_fraud_label": [0, 1, 1, 0, 0, 0, 0, 0],
            "fraud_probability": [0.1, 0.8, 0.7, 0.4, 0.1, 0.2, 0.1, 0.2],
            "selected_threshold": 0.5,
        }
    )
    output = calculate_fraud_model_monitoring(frame, _config())
    assert {"precision", "recall", "average_precision"} <= set(output.metric_name)


def test_aml_excessive_coverage_and_concentration_warn() -> None:
    alerts = pd.DataFrame(
        {
            "alert_id": [f"A{i}" for i in range(10)],
            "transaction_id": [f"T{i}" for i in range(10)],
            "customer_id": [f"C{i % 2}" for i in range(10)],
            "rule_id": ["AML001"] * 9 + ["AML002"],
        }
    )
    output = calculate_aml_rule_monitoring(alerts, 10, 2, _config())
    assert output.query("metric_name == 'alerted_transaction_rate'").iloc[0].status == "critical"
    assert output.query("metric_name == 'dominant_rule_concentration'").iloc[0].status == "warning"


def test_risk_shift_and_reconstruction_are_monitored() -> None:
    scores = pd.DataFrame(
        {
            "customer_id": [f"C{i}" for i in range(4)],
            "total_risk_score": [10, 20, 80, 90],
            "risk_band": ["low", "low", "critical", "critical"],
            "score_version": "1",
        }
    )
    components = pd.DataFrame(
        {"customer_id": [f"C{i}" for i in range(4)], "weighted_contribution": [10, 20, 80, 90]}
    )
    output = calculate_customer_risk_monitoring(
        scores, components, {"weights_reconstruct_total": True}, _config()
    )
    assert output.query("metric_name == 'risk_band_distribution_shift'").iloc[0].status == "warning"


def test_explanation_and_genai_integrity_failures_are_critical() -> None:
    explanation = calculate_explainability_monitoring(
        {
            "transactions_explained": 1,
            "explanations_failed": 1,
            "excluded_feature_violations": ["id"],
            "maximum_decision_score_difference": 1,
            "maximum_probability_difference": 1,
            "invalid_reason_code_count": 0,
            "missing_feature_count": 0,
        },
        _config(),
    )
    assert "critical" in set(explanation.status)
    genai = calculate_genai_monitoring(
        {"cases_generated": 1, "grounding_checks_failed": 1, "safety_checks_failed": 0},
        [{"network_call_enabled": True}],
        _config(),
    )
    assert genai.query("metric_name == 'network_enabled_payloads'").iloc[0].status == "critical"


def test_pipeline_missing_artifact_is_unavailable(tmp_path: Path) -> None:
    config = _config()
    config["expected_pipeline_stages"] = {"missing": str(tmp_path / "none.json")}
    config["expected_artefacts"] = []
    output = check_pipeline_and_artefacts(config)
    assert output.iloc[0].status == "unavailable"


def test_alert_ids_evidence_and_overall_status_are_deterministic() -> None:
    config = _config()
    first = create_monitoring_alert(
        "aml", "volume", "rate", 1, 0, 0.5, "warning", "reason", "Human review.", {"x": 1}, config
    )
    second = create_monitoring_alert(
        "aml", "volume", "rate", 1, 0, 0.5, "warning", "reason", "Human review.", {"x": 1}, config
    )
    assert first == second
    assert json.loads(first["evidence_json"]) == {"x": 1}
    assert aggregate_platform_status({"x": pd.DataFrame({"status": ["warning"]})}) == "warning"
    assert aggregate_platform_status({"x": pd.DataFrame({"status": ["critical"]})}) == "critical"


def test_outputs_write_to_temporary_directory(tmp_path: Path) -> None:
    config = _config()
    keys = [
        "data_quality_output_path",
        "numeric_drift_output_path",
        "categorical_drift_output_path",
        "fraud_monitoring_output_path",
        "aml_monitoring_output_path",
        "risk_monitoring_output_path",
        "explainability_monitoring_output_path",
        "genai_monitoring_output_path",
        "pipeline_health_output_path",
        "alerts_output_path",
        "summary_output_path",
        "report_output_path",
    ]
    for key in keys:
        config[key] = str(tmp_path / Path(config[key]).name)
    domains = {
        name: pd.DataFrame({"metric_name": [name], "status": ["healthy"]})
        for name in [
            "data_quality",
            "numeric_drift",
            "categorical_drift",
            "fraud_model",
            "aml",
            "customer_risk",
            "explainability",
            "genai",
            "pipeline",
        ]
    }
    summary = {
        "overall_platform_status": "healthy",
        "baseline_period": "a",
        "current_period": "b",
        "healthy_control_count": 9,
        "warning_count": 0,
        "critical_count": 0,
        "unavailable_count": 0,
        "domain_statuses": {name: "healthy" for name in domains},
    }
    paths = write_monitoring_outputs(domains, pd.DataFrame(), summary, config)
    assert all(path.exists() for path in paths.values())
