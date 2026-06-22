from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from src.models.train_fraud_baseline import (
    build_prediction_output,
    build_threshold_analysis,
    calculate_evaluation_metrics,
    chronological_train_test_split,
    extract_model_coefficients,
    generate_fraud_probabilities,
    load_transaction_features,
    save_model_artifacts,
    select_operating_threshold,
    select_predictive_feature_columns,
    train_and_evaluate,
    train_fraud_model,
    validate_target,
    write_model_outputs,
    write_model_report,
)


def _config(tmp_path: Path | None = None) -> dict:
    root = tmp_path or Path(".")
    return {
        "input_path": str(root / "transaction_features.csv"),
        "feature_dictionary_path": str(root / "feature_dictionary.csv"),
        "model_output_dir": str(root / "models"),
        "report_output_dir": str(root / "reports"),
        "prediction_output_path": str(root / "outputs" / "fraud_test_predictions.csv"),
        "threshold_analysis_output_path": str(
            root / "outputs" / "fraud_threshold_analysis.csv"
        ),
        "feature_list_output_path": str(root / "outputs" / "fraud_feature_list.json"),
        "metrics_output_path": str(root / "outputs" / "fraud_model_metrics.json"),
        "coefficients_output_path": str(root / "outputs" / "fraud_model_coefficients.csv"),
        "target_column": "fraud_label",
        "timestamp_column": "transaction_timestamp",
        "id_columns": [
            "transaction_id",
            "account_id",
            "customer_id",
            "device_id",
            "session_id",
        ],
        "excluded_feature_columns": [
            "fraud_typology",
            "label_confidence",
            "label_source",
            "transaction_status",
        ],
        "test_fraction": 0.25,
        "random_state": 42,
        "max_iterations": 500,
        "class_weight": "balanced",
        "default_threshold": 0.5,
        "threshold_selection_metric": "f1",
        "minimum_precision": 0.1,
        "top_feature_count": 3,
    }


def _features() -> pd.DataFrame:
    row_count = 40
    index = np.arange(row_count)
    return pd.DataFrame(
        {
            "transaction_id": [f"TXN-{value:04d}" for value in index],
            "account_id": [f"ACC-{value % 8:03d}" for value in index],
            "customer_id": [f"CUST-{value % 10:03d}" for value in index],
            "device_id": [f"DEV-{value % 6:03d}" for value in index],
            "session_id": [f"SES-{value:04d}" for value in index],
            "transaction_timestamp": pd.date_range("2025-01-01", periods=row_count, freq="h"),
            "amount": 10.0 + index * 2.5,
            "transaction_hour": index % 24,
            "transaction_velocity_score": (index % 7) / 2,
            "channel": np.where(index % 2 == 0, "Mobile App", "ATM"),
            "merchant_category": np.where(index % 3 == 0, "Travel", "Grocery"),
            "transaction_status": np.where(index % 9 == 0, "Declined", "Approved"),
            "risky_outcome": index % 2,
            "fraud_label": (index % 5 == 4).astype(int),
            "fraud_typology": np.where(index % 5 == 4, "Synthetic Fraud", "Not Fraud"),
            "label_confidence": 0.9,
            "label_source": "Synthetic Rule",
        }
    )


def _dictionary() -> pd.DataFrame:
    rows = []
    for column in _features().columns:
        category = "label" if column in {"fraud_label", "fraud_typology"} else "behavioural"
        leakage = "high - outcome only" if column in {"fraud_label", "risky_outcome"} else "low"
        rows.append(
            {
                "feature_name": column,
                "feature_table": "transaction_features",
                "category": category,
                "leakage_risk": leakage,
            }
        )
    return pd.DataFrame(rows)


def test_transaction_features_load_and_target_is_valid(tmp_path: Path) -> None:
    path = tmp_path / "features.csv"
    _features().to_csv(path, index=False)

    loaded = load_transaction_features(path)
    target = validate_target(loaded, "fraud_label")

    assert len(loaded) == 40
    assert set(target.unique()) == {0, 1}


def test_identifiers_labels_and_high_leakage_features_are_excluded() -> None:
    selected = select_predictive_feature_columns(_features(), _config(), _dictionary())

    assert "amount" in selected
    assert "transaction_id" not in selected
    assert "transaction_timestamp" not in selected
    assert "transaction_status" not in selected
    assert "fraud_label" not in selected
    assert "fraud_typology" not in selected
    assert "risky_outcome" not in selected


def test_chronological_split_preserves_time_order() -> None:
    shuffled = _features().sample(frac=1, random_state=3)
    train, test, boundary = chronological_train_test_split(
        shuffled, "transaction_timestamp", "fraud_label", 0.25
    )

    assert len(train) == 30
    assert len(test) == 10
    assert train["transaction_timestamp"].max() <= test["transaction_timestamp"].min()
    assert boundary == test["transaction_timestamp"].min().isoformat()


def test_pipeline_fits_and_returns_valid_probabilities() -> None:
    dataframe = _features()
    config = _config()
    selected = select_predictive_feature_columns(dataframe, config, _dictionary())
    train, test, _ = chronological_train_test_split(
        dataframe, "transaction_timestamp", "fraud_label", 0.25
    )
    pipeline = train_fraud_model(train, selected, "fraud_label", config)
    probabilities = generate_fraud_probabilities(pipeline, test, selected)

    assert len(probabilities) == len(test)
    assert np.all((probabilities >= 0) & (probabilities <= 1))


def test_threshold_analysis_selection_and_metrics_are_valid() -> None:
    actual = np.array([0, 0, 1, 1])
    probabilities = np.array([0.1, 0.4, 0.6, 0.9])
    analysis = build_threshold_analysis(actual, probabilities, np.array([0.25, 0.5, 0.75]))
    threshold = select_operating_threshold(analysis, "f1", 0.1, 0.5)
    predictions = (probabilities >= threshold).astype(int)
    metrics = calculate_evaluation_metrics(
        actual, probabilities, predictions, threshold, np.array([0, 1, 0, 1])
    )

    assert analysis["threshold"].between(0, 1).all()
    assert 0 <= threshold <= 1
    assert {
        "precision",
        "recall",
        "f1_score",
        "roc_auc",
        "average_precision",
        "confusion_matrix",
        "false_positive_rate",
        "false_negative_rate",
    } <= metrics.keys()


def test_predictions_and_coefficients_have_required_columns() -> None:
    result = train_and_evaluate(_features(), _dictionary(), _config())

    assert {
        "transaction_id",
        "transaction_timestamp",
        "actual_fraud_label",
        "fraud_probability",
        "predicted_fraud_label",
        "selected_threshold",
        "error_type",
    } <= set(result["predictions"].columns)
    assert {
        "transformed_feature_name",
        "coefficient",
        "absolute_coefficient",
        "direction",
        "rank",
    } <= set(result["coefficients"].columns)


def test_outputs_can_be_written(tmp_path: Path) -> None:
    config = _config(tmp_path)
    result = train_and_evaluate(_features(), _dictionary(), config)
    model_paths = save_model_artifacts(
        result["pipeline"], result["metadata"], config["model_output_dir"]
    )
    output_paths = write_model_outputs(
        result["predictions"],
        result["threshold_analysis"],
        result["feature_columns"],
        result["metrics"],
        result["coefficients"],
        config,
    )
    report_path = tmp_path / "reports" / "fraud_baseline_model_report.md"
    write_model_report(
        result["metrics"],
        result["coefficients"],
        len(result["feature_columns"]),
        result["split_boundary"],
        report_path,
        3,
    )

    assert all(path.exists() and path.stat().st_size > 0 for path in model_paths.values())
    assert all(path.exists() and path.stat().st_size > 0 for path in output_paths.values())
    assert report_path.exists()


def test_training_is_deterministic() -> None:
    first = train_and_evaluate(_features(), _dictionary(), _config())
    second = train_and_evaluate(_features(), _dictionary(), _config())

    np.testing.assert_allclose(
        first["predictions"]["fraud_probability"],
        second["predictions"]["fraud_probability"],
    )
    pd.testing.assert_frame_equal(first["coefficients"], second["coefficients"])
    assert first["selected_threshold"] == second["selected_threshold"]


def test_invalid_and_single_class_targets_raise_clear_errors() -> None:
    invalid = _features()
    invalid.loc[0, "fraud_label"] = 3
    with pytest.raises(ValueError, match="must be binary"):
        validate_target(invalid, "fraud_label")

    single_class = _features()
    single_class["fraud_label"] = 0
    with pytest.raises(ValueError, match="must contain both fraud classes"):
        validate_target(single_class, "fraud_label")


def test_prediction_builder_assigns_error_types() -> None:
    test = _features().iloc[:4].copy()
    test["fraud_label"] = [1, 0, 0, 1]
    probabilities = np.array([0.9, 0.8, 0.2, 0.1])
    predictions = np.array([1, 1, 0, 0])
    output = build_prediction_output(
        test,
        probabilities,
        predictions,
        0.5,
        "fraud_label",
        "transaction_timestamp",
    )

    assert output["error_type"].tolist() == [
        "true_positive",
        "false_positive",
        "true_negative",
        "false_negative",
    ]


def test_coefficients_can_be_extracted_directly() -> None:
    result = train_and_evaluate(_features(), _dictionary(), _config())
    coefficients = extract_model_coefficients(result["pipeline"])

    assert not coefficients.empty
    assert coefficients["rank"].is_monotonic_increasing
