import json
from copy import deepcopy
from pathlib import Path

import pandas as pd
import pytest
from src.aml_rules.aml_rule_engine import (
    ALERT_COLUMNS,
    RULE_EVALUATORS,
    aggregate_alerts_by_customer,
    build_rule_summary,
    evaluate_all_enabled_rules,
    evaluate_aml001,
    evaluate_aml002,
    evaluate_aml003,
    evaluate_aml004,
    evaluate_aml005,
    evaluate_aml006,
    evaluate_aml007,
    evaluate_aml008,
    evaluate_aml009,
    evaluate_aml010,
    generate_aml_summary_metrics,
    load_aml_config,
    write_aml_outputs,
    write_aml_report,
)


def _config() -> dict:
    config = deepcopy(load_aml_config())
    config.update(
        {
            "high_value_transaction_threshold": 500.0,
            "structuring_reporting_threshold": 1000.0,
            "structuring_aggregate_threshold": 300.0,
            "structuring_window_hours": 24,
            "structuring_minimum_transaction_count": 3,
            "rapid_movement_window_minutes": 60,
            "rapid_movement_minimum_amount": 100.0,
            "cross_border_window_days": 7,
            "cross_border_count_threshold": 2,
            "cross_border_ratio_threshold": 0.5,
            "dormant_account_days": 60,
            "dormant_reactivation_amount": 200.0,
            "failed_transaction_window_hours": 24,
            "failed_transaction_count_threshold": 2,
            "customer_alert_threshold": 80,
            "critical_alert_threshold": 160,
        }
    )
    return config


def _data(rows: list[dict] | None = None) -> pd.DataFrame:
    defaults = {
        "transaction_id": "TXN-001",
        "account_id": "ACC-001",
        "customer_id": "CUST-001",
        "transaction_timestamp": pd.Timestamp("2025-01-01T12:00:00"),
        "amount": 25.0,
        "transaction_type": "Card Purchase",
        "channel": "Branch",
        "merchant_category": "Grocery",
        "merchant_country": "GB",
        "is_cross_border": False,
        "transaction_status": "Approved",
        "device_id": "DEV-001",
        "session_id": "SES-001",
        "ip_country": "GB",
        "login_success": True,
        "authentication_method": "MFA Push",
        "session_risk_signal": "Low",
        "customer_country": "GB",
        "kyc_status": "Verified",
        "pep_flag": False,
        "sanctions_screening_status": "Clear",
        "account_status": "Active",
        "new_device_flag": 0,
        "country_mismatch_flag": 0,
        "aml_watchlist_flag": 0,
    }
    source_rows = rows or [{}]
    output = []
    for index, updates in enumerate(source_rows, start=1):
        row = defaults | {"transaction_id": f"TXN-{index:03d}"} | updates
        output.append(row)
    return pd.DataFrame(output).sort_values("transaction_timestamp").reset_index(drop=True)


def _assert_rule_alert(alerts: pd.DataFrame, rule_id: str, config: dict) -> None:
    assert list(alerts.columns) == ALERT_COLUMNS
    assert not alerts.empty
    assert set(alerts["rule_id"]) == {rule_id}
    assert set(alerts["risk_points"]) == {config["rule_risk_points"][rule_id]}
    assert all(json.loads(value) for value in alerts["evidence_json"])


def test_configuration_loads_and_enabled_rules_are_recognised() -> None:
    config = load_aml_config()

    assert len(config["enabled_rules"]) == 10
    assert set(config["enabled_rules"]) == set(RULE_EVALUATORS)


def test_every_rule_returns_expected_schema_for_empty_results() -> None:
    config = _config()
    controlled = _data()

    for evaluator in RULE_EVALUATORS.values():
        assert list(evaluator(controlled, config).columns) == ALERT_COLUMNS


def test_high_value_transaction_triggers_aml001() -> None:
    config = _config()
    alerts = evaluate_aml001(_data([{"amount": 600.0}]), config)
    _assert_rule_alert(alerts, "AML001", config)


def test_structuring_pattern_triggers_aml002() -> None:
    config = _config()
    rows = [
        {"transaction_timestamp": pd.Timestamp("2025-01-01T10:00:00"), "amount": 110.0},
        {"transaction_timestamp": pd.Timestamp("2025-01-01T11:00:00"), "amount": 120.0},
        {"transaction_timestamp": pd.Timestamp("2025-01-01T12:00:00"), "amount": 130.0},
    ]
    alerts = evaluate_aml002(_data(rows), config)
    _assert_rule_alert(alerts, "AML002", config)
    assert len(alerts) == 1


def test_rapid_movement_triggers_aml003() -> None:
    config = _config()
    rows = [
        {"transaction_timestamp": pd.Timestamp("2025-01-01T10:00:00"), "amount": 120.0},
        {"transaction_timestamp": pd.Timestamp("2025-01-01T10:20:00"), "amount": 150.0},
    ]
    _assert_rule_alert(evaluate_aml003(_data(rows), config), "AML003", config)


def test_high_risk_geography_triggers_aml004() -> None:
    config = _config()
    alerts = evaluate_aml004(_data([{"merchant_country": "BR"}]), config)
    _assert_rule_alert(alerts, "AML004", config)


def test_cross_border_activity_triggers_aml005() -> None:
    config = _config()
    rows = [
        {
            "transaction_timestamp": pd.Timestamp("2025-01-01") + pd.Timedelta(hours=index),
            "is_cross_border": True,
            "merchant_country": country,
        }
        for index, country in enumerate(["FR", "DE", "ES"])
    ]
    alerts = evaluate_aml005(_data(rows), config)
    _assert_rule_alert(alerts, "AML005", config)


def test_dormant_reactivation_triggers_aml006() -> None:
    config = _config()
    rows = [
        {"transaction_timestamp": pd.Timestamp("2025-01-01"), "amount": 20.0},
        {"transaction_timestamp": pd.Timestamp("2025-04-01"), "amount": 250.0},
    ]
    alerts = evaluate_aml006(_data(rows), config)
    _assert_rule_alert(alerts, "AML006", config)


def test_repeated_failures_trigger_aml007() -> None:
    config = _config()
    rows = [
        {
            "transaction_timestamp": pd.Timestamp("2025-01-01T10:00:00"),
            "transaction_status": "Declined",
        },
        {
            "transaction_timestamp": pd.Timestamp("2025-01-01T11:00:00"),
            "transaction_status": "Reversed",
        },
    ]
    alerts = evaluate_aml007(_data(rows), config)
    _assert_rule_alert(alerts, "AML007", config)


def test_risky_device_or_session_triggers_aml008() -> None:
    config = _config()
    alerts = evaluate_aml008(_data([{"new_device_flag": 1}]), config)
    _assert_rule_alert(alerts, "AML008", config)


def test_kyc_or_watchlist_exposure_triggers_aml009() -> None:
    config = _config()
    alerts = evaluate_aml009(_data([{"kyc_status": "Pending Review"}]), config)
    _assert_rule_alert(alerts, "AML009", config)


def test_merchant_or_channel_pattern_triggers_aml010() -> None:
    config = _config()
    alerts = evaluate_aml010(_data([{"merchant_category": "Crypto Exchange"}]), config)
    _assert_rule_alert(alerts, "AML010", config)


def test_controlled_transaction_creates_no_alerts() -> None:
    alerts = evaluate_all_enabled_rules(_data(), _config())
    assert alerts.empty
    assert list(alerts.columns) == ALERT_COLUMNS


def test_alert_ids_and_evidence_are_deterministic() -> None:
    config = _config()
    data = _data([{"amount": 600.0}])
    first = evaluate_aml001(data, config)
    second = evaluate_aml001(data, config)

    assert first.loc[0, "alert_id"] == second.loc[0, "alert_id"]
    assert first.loc[0, "evidence_json"] == second.loc[0, "evidence_json"]
    assert json.loads(first.loc[0, "evidence_json"])["configured_threshold"] == 500.0


def test_customer_summary_aggregates_and_priorities_are_valid() -> None:
    config = _config()
    data = _data([{"amount": 600.0, "merchant_category": "Crypto Exchange"}])
    alerts = evaluate_all_enabled_rules(data, config)
    summary = aggregate_alerts_by_customer(alerts, config)

    assert summary.loc[0, "total_aml_alerts"] == len(alerts)
    assert summary.loc[0, "total_aml_risk_points"] == alerts["risk_points"].sum()
    assert summary.loc[0, "recommended_review_priority"] in {
        "routine",
        "standard",
        "enhanced",
        "urgent",
    }


def test_outputs_can_be_written_to_temporary_directory(tmp_path: Path) -> None:
    config = _config()
    config.update(
        {
            "alerts_output_path": str(tmp_path / "outputs" / "alerts.csv"),
            "customer_summary_output_path": str(tmp_path / "outputs" / "customers.csv"),
            "rule_summary_output_path": str(tmp_path / "outputs" / "rules.csv"),
            "run_summary_output_path": str(tmp_path / "outputs" / "run.json"),
        }
    )
    data = _data([{"amount": 600.0}])
    alerts = evaluate_all_enabled_rules(data, config)
    customers = aggregate_alerts_by_customer(alerts, config)
    rules = build_rule_summary(alerts, len(data), config)
    run = generate_aml_summary_metrics(data, alerts, customers, config)
    paths = write_aml_outputs(alerts, customers, rules, run, config)
    report_path = tmp_path / "reports" / "aml.md"
    write_aml_report(run, rules, report_path)

    assert all(path.exists() and path.stat().st_size > 0 for path in paths.values())
    assert report_path.exists()


def test_malformed_inputs_raise_clear_errors() -> None:
    malformed = _data().drop(columns="customer_id")
    with pytest.raises(ValueError, match="prepared AML data is missing required columns"):
        evaluate_all_enabled_rules(malformed, _config())
