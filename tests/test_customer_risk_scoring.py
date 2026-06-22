import json
from copy import deepcopy
from pathlib import Path

import pandas as pd
import pytest
from src.risk_scoring.customer_risk_scoring import (
    COMPONENTS,
    assign_review_priority,
    assign_risk_band,
    calculate_customer_risk_scores,
    generate_portfolio_risk_summary,
    generate_retrospective_evaluation,
    load_customer_feature_data,
    load_risk_config,
    prepare_aml_alert_risk_indicators,
    prepare_device_session_risk_indicators,
    prepare_fraud_model_risk_indicators,
    prepare_kyc_risk_indicators,
    prepare_transaction_behaviour_risk_indicators,
    validate_risk_config,
    write_risk_outputs,
    write_risk_report,
)


def _config() -> dict:
    return deepcopy(load_risk_config())


def _indicators() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "customer_id": "CUST-001",
                "kyc_status": "Verified",
                "pep_flag": False,
                "sanctions_screening_status": "Clear",
                "customer_risk_rating": "Low",
                "aml_watchlist_flag": 0,
                "customer_tenure_days": 1500,
                "total_transaction_count": 10,
                "total_transaction_amount": 500.0,
                "maximum_transaction_amount": 100.0,
                "cross_border_ratio": 0.1,
                "failed_transaction_ratio": 0.0,
                "night_transaction_ratio": 0.1,
                "unique_merchant_country_count": 2,
                "new_device_transaction_count": 1,
                "maximum_transaction_velocity": 0.2,
                "total_aml_alerts": 0,
                "distinct_rules_triggered": 0,
                "low_severity_alerts": 0,
                "medium_severity_alerts": 0,
                "high_severity_alerts": 0,
                "critical_severity_alerts": 0,
                "total_aml_risk_points": 0,
                "maximum_aml_severity": "none",
                "high_value_alert_count": 0,
                "structuring_alert_count": 0,
                "geography_alert_count": 0,
                "device_session_alert_count": 0,
                "kyc_watchlist_alert_count": 0,
                "maximum_fraud_probability": 0.1,
                "average_fraud_probability": 0.05,
                "predicted_fraud_transaction_count": 0,
                "high_probability_transaction_count": 0,
                "predicted_fraud_transaction_ratio": 0.0,
                "high_probability_transaction_ratio": 0.0,
                "risky_session_count": 0,
                "unique_device_count": 1,
                "failed_authentication_count": 0,
                "geography_mismatch_count": 0,
                "elevated_session_count": 0,
            },
            {
                "customer_id": "CUST-002",
                "kyc_status": "Pending Review",
                "pep_flag": True,
                "sanctions_screening_status": "Potential Match",
                "customer_risk_rating": "High",
                "aml_watchlist_flag": 1,
                "customer_tenure_days": 100,
                "total_transaction_count": 60,
                "total_transaction_amount": 8000.0,
                "maximum_transaction_amount": 1200.0,
                "cross_border_ratio": 0.95,
                "failed_transaction_ratio": 0.2,
                "night_transaction_ratio": 0.5,
                "unique_merchant_country_count": 15,
                "new_device_transaction_count": 8,
                "maximum_transaction_velocity": 4.0,
                "total_aml_alerts": 20,
                "distinct_rules_triggered": 7,
                "low_severity_alerts": 3,
                "medium_severity_alerts": 8,
                "high_severity_alerts": 8,
                "critical_severity_alerts": 1,
                "total_aml_risk_points": 1800,
                "maximum_aml_severity": "critical",
                "high_value_alert_count": 2,
                "structuring_alert_count": 4,
                "geography_alert_count": 6,
                "device_session_alert_count": 3,
                "kyc_watchlist_alert_count": 2,
                "maximum_fraud_probability": 0.9,
                "average_fraud_probability": 0.7,
                "predicted_fraud_transaction_count": 8,
                "high_probability_transaction_count": 5,
                "predicted_fraud_transaction_ratio": 0.8,
                "high_probability_transaction_ratio": 0.5,
                "risky_session_count": 6,
                "unique_device_count": 7,
                "failed_authentication_count": 2,
                "geography_mismatch_count": 10,
                "elevated_session_count": 2,
            },
        ]
    )


def test_configuration_loads_and_weights_sum_to_one() -> None:
    config = load_risk_config()
    assert sum(config["component_weights"].values()) == pytest.approx(1.0)


def test_invalid_weights_raise_clear_error() -> None:
    config = _config()
    config["component_weights"]["kyc"] = 0.5
    with pytest.raises(ValueError, match="must sum to 1.0"):
        validate_risk_config(config)


def test_required_inputs_are_validated() -> None:
    malformed = _indicators().drop(columns="kyc_status")
    with pytest.raises(ValueError, match="missing required columns.*kyc_status"):
        prepare_kyc_risk_indicators(malformed, _config())


def test_every_customer_receives_five_bounded_components_and_total() -> None:
    scores, components = calculate_customer_risk_scores(_indicators(), _config())

    assert len(components) == len(scores) * 5
    assert set(components["component_name"]) == set(COMPONENTS)
    assert components["normalised_score"].between(0, 100).all()
    assert scores["total_risk_score"].between(0, 100).all()


def test_weighted_contributions_reconstruct_total_score() -> None:
    scores, components = calculate_customer_risk_scores(_indicators(), _config())
    reconstructed = components.groupby("customer_id")["weighted_contribution"].sum()
    expected = scores.set_index("customer_id")["total_risk_score"]
    pd.testing.assert_series_equal(reconstructed, expected, check_names=False)


@pytest.mark.parametrize(
    ("score", "expected"),
    [(29.99, "low"), (30.0, "moderate"), (55.0, "high"), (75.0, "critical")],
)
def test_risk_bands_are_assigned_at_boundaries(score: float, expected: str) -> None:
    assert assign_risk_band(score, _config()) == expected


def test_review_priorities_use_allowed_domain() -> None:
    values = [assign_review_priority(score, _config()) for score in (0, 25, 50, 75, 100)]
    assert set(values) <= {"routine", "standard", "enhanced", "urgent"}


def test_aml_alerts_increase_aml_component_risk() -> None:
    components = prepare_aml_alert_risk_indicators(_indicators(), _config())
    assert components.iloc[1]["normalised_score"] > components.iloc[0]["normalised_score"]


def test_higher_fraud_probabilities_increase_fraud_component_risk() -> None:
    components = prepare_fraud_model_risk_indicators(_indicators(), _config())
    assert components.iloc[1]["normalised_score"] > components.iloc[0]["normalised_score"]


def test_kyc_pep_sanctions_and_watchlist_affect_kyc_risk() -> None:
    components = prepare_kyc_risk_indicators(_indicators(), _config())
    assert components.iloc[1]["normalised_score"] > components.iloc[0]["normalised_score"]


def test_risky_sessions_increase_device_risk() -> None:
    components = prepare_device_session_risk_indicators(_indicators(), _config())
    assert components.iloc[1]["normalised_score"] > components.iloc[0]["normalised_score"]


def test_transaction_thresholds_increase_behaviour_risk() -> None:
    components = prepare_transaction_behaviour_risk_indicators(_indicators(), _config())
    assert components.iloc[1]["normalised_score"] > components.iloc[0]["normalised_score"]


def test_reasons_are_deterministic_and_evidence_is_valid_json() -> None:
    first_scores, first_components = calculate_customer_risk_scores(_indicators(), _config())
    second_scores, second_components = calculate_customer_risk_scores(_indicators(), _config())

    pd.testing.assert_frame_equal(first_scores, second_scores)
    pd.testing.assert_frame_equal(first_components, second_components)
    assert first_scores["top_risk_reasons_json"].map(json.loads).notna().all()
    assert first_scores["component_evidence_json"].map(json.loads).notna().all()
    assert first_components["evidence_json"].map(json.loads).notna().all()


def test_actual_fraud_labels_are_rejected_by_scoring() -> None:
    indicators = _indicators()
    indicators["fraud_label"] = [0, 1]
    with pytest.raises(ValueError, match="fraud labels are prohibited"):
        calculate_customer_risk_scores(indicators, _config())


def test_retrospective_evaluation_is_separate() -> None:
    scores, _ = calculate_customer_risk_scores(_indicators(), _config())
    transaction_features = pd.DataFrame(
        {"transaction_id": ["T1", "T2"], "customer_id": ["CUST-001", "CUST-002"]}
    )
    labels = pd.DataFrame({"transaction_id": ["T1", "T2"], "fraud_label": [0, 1]})
    evaluation = generate_retrospective_evaluation(scores, labels, transaction_features)

    assert evaluation["evaluation_type"] == "retrospective_only"
    assert evaluation["labels_used_in_scoring"] is False


def test_customer_feature_loader_removes_historical_label_columns(tmp_path: Path) -> None:
    path = tmp_path / "features.csv"
    pd.DataFrame(
        {
            "customer_id": ["C1"],
            "total_transaction_count": [1],
            "cross_border_ratio": [0.0],
            "historical_fraud_count": [1],
        }
    ).to_csv(path, index=False)

    loaded = load_customer_feature_data(path)
    assert "historical_fraud_count" not in loaded.columns


def test_outputs_can_be_written_to_temporary_directory(tmp_path: Path) -> None:
    config = _config()
    config.update(
        {
            "risk_scores_output_path": str(tmp_path / "outputs" / "scores.csv"),
            "components_output_path": str(tmp_path / "outputs" / "components.csv"),
            "summary_output_path": str(tmp_path / "outputs" / "summary.json"),
            "retrospective_output_path": str(tmp_path / "outputs" / "retro.json"),
        }
    )
    scores, components = calculate_customer_risk_scores(_indicators(), config)
    summary = generate_portfolio_risk_summary(scores, components, {}, config)
    retrospective = {"evaluation_type": "retrospective_only", "labels_used_in_scoring": False}
    paths = write_risk_outputs(scores, components, summary, retrospective, config)
    report_path = tmp_path / "reports" / "risk.md"
    write_risk_report(summary, config, report_path)

    assert all(path.exists() and path.stat().st_size > 0 for path in paths.values())
    assert report_path.exists()
