from pathlib import Path

import pandas as pd
import pytest
from src.data_generation.generate_banking_data import generate_all_datasets, write_all_datasets
from src.features.build_features import (
    build_feature_summary,
    build_final_feature_datasets,
    get_predictive_transaction_columns,
    write_feature_outputs,
    write_feature_quality_outputs,
)
from src.ingestion.load_banking_data import load_all_datasets

GENERATION_CONFIG = {
    "random_seed": 23,
    "number_of_customers": 10,
    "accounts_per_customer_min": 1,
    "accounts_per_customer_max": 2,
    "transactions_per_account_min": 3,
    "transactions_per_account_max": 5,
    "output_dir": "data/raw",
    "fraud_rate": 0.2,
    "aml_watchlist_rate": 0.2,
}

FEATURE_CONFIG = {
    "input_dir": "data/raw",
    "output_dir": "data/processed",
    "reference_timestamp": "2026-01-01T00:00:00",
    "velocity_window_hours": 24,
    "behaviour_window_days": 7,
    "night_start_hour": 22,
    "night_end_hour": 6,
    "rapid_transaction_minutes": 10,
    "high_value_transaction_threshold": 1000.0,
    "high_risk_channels": ["ATM", "Online Banking"],
    "high_risk_merchant_categories": [
        "Crypto Exchange",
        "Money Transfer",
        "Cash Services",
    ],
    "high_risk_countries": ["BR", "TR", "ZA"],
    "include_label_columns": True,
}


def _build_test_features(tmp_path: Path):
    raw_dir = tmp_path / "raw"
    generated = generate_all_datasets(GENERATION_CONFIG)
    write_all_datasets(raw_dir, generated)
    datasets = load_all_datasets(raw_dir)
    return datasets, build_final_feature_datasets(datasets, FEATURE_CONFIG)


def test_feature_tables_are_non_empty_and_keys_are_unique(tmp_path: Path) -> None:
    _, features = _build_test_features(tmp_path)

    assert not features["transaction_features"].empty
    assert not features["account_features"].empty
    assert not features["customer_features"].empty
    assert features["transaction_features"]["transaction_id"].is_unique
    assert features["account_features"]["account_id"].is_unique
    assert features["customer_features"]["customer_id"].is_unique


def test_expected_feature_columns_exist(tmp_path: Path) -> None:
    _, features = _build_test_features(tmp_path)
    transaction_columns = set(features["transaction_features"].columns)
    account_columns = set(features["account_features"].columns)
    customer_columns = set(features["customer_features"].columns)

    assert {
        "transaction_hour",
        "amount_vs_account_average",
        "transaction_count_customer_24h",
        "distinct_countries_customer_7d",
        "new_device_flag",
        "risky_session_flag",
        "transaction_velocity_score",
    } <= transaction_columns
    assert {
        "transaction_count",
        "account_age_days",
        "account_status_encoded",
        "account_type_encoded",
    } <= account_columns
    assert {
        "number_of_accounts",
        "cross_border_ratio",
        "aml_watchlist_flag",
        "kyc_status_encoded",
        "historical_fraud_rate",
    } <= customer_columns


def test_velocity_features_are_numeric_and_non_negative(tmp_path: Path) -> None:
    _, features = _build_test_features(tmp_path)
    transactions = features["transaction_features"]
    velocity_columns = [
        "transaction_count_customer_24h",
        "transaction_amount_customer_24h",
        "transaction_count_account_24h",
        "transaction_amount_account_24h",
        "transaction_velocity_score",
    ]

    assert all(pd.api.types.is_numeric_dtype(transactions[column]) for column in velocity_columns)
    assert (transactions[velocity_columns] >= 0).all().all()


def test_customer_ratios_are_within_valid_bounds(tmp_path: Path) -> None:
    _, features = _build_test_features(tmp_path)
    customers = features["customer_features"]
    ratio_columns = [
        "cross_border_ratio",
        "failed_transaction_ratio",
        "night_transaction_ratio",
        "historical_fraud_rate",
    ]

    assert customers[ratio_columns].apply(lambda column: column.between(0, 1).all()).all()


def test_feature_generation_is_deterministic(tmp_path: Path) -> None:
    datasets, first = _build_test_features(tmp_path)
    second = build_final_feature_datasets(datasets, FEATURE_CONFIG)

    for table_name in first:
        pd.testing.assert_frame_equal(first[table_name], second[table_name])


def test_fraud_label_is_excluded_from_predictive_columns(tmp_path: Path) -> None:
    _, features = _build_test_features(tmp_path)
    transactions = features["transaction_features"]
    predictive_columns = get_predictive_transaction_columns(transactions)

    assert "fraud_label" in transactions.columns
    assert "fraud_label" not in predictive_columns
    assert "fraud_typology" not in predictive_columns
    label_dictionary = features["feature_dictionary"].query("feature_name == 'fraud_label'")
    assert label_dictionary.iloc[0]["category"] == "label"


def test_malformed_input_produces_clear_error(tmp_path: Path) -> None:
    datasets, _ = _build_test_features(tmp_path)
    datasets["transactions"] = datasets["transactions"].drop(columns="amount")

    with pytest.raises(ValueError, match="transactions is missing required columns.*amount"):
        build_final_feature_datasets(datasets, FEATURE_CONFIG)


def test_feature_outputs_and_reports_can_be_written(tmp_path: Path) -> None:
    datasets, features = _build_test_features(tmp_path)
    paths = write_feature_outputs(features, tmp_path / "processed")
    summary = build_feature_summary(datasets, features)
    report_path = tmp_path / "reports" / "feature_engineering_report.md"
    summary_path = tmp_path / "outputs" / "feature_engineering_summary.json"
    write_feature_quality_outputs(summary, report_path, summary_path)

    assert all(path.exists() and path.stat().st_size > 0 for path in paths.values())
    assert report_path.exists()
    assert summary_path.exists()
    assert summary["overall_status"] == "passed"
