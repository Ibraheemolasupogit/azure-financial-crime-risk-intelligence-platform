import json
from copy import deepcopy
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from src.explainability.explain_fraud_model import (
    CONTRIBUTION_COLUMNS,
    EXCLUDED_FEATURES,
    GLOBAL_COLUMNS,
    aggregate_global_source_importance,
    build_error_type_analysis,
    build_explainability_summary,
    calculate_global_feature_importance,
    calculate_local_explanations,
    extract_logistic_coefficients,
    identify_transformed_features,
    load_explainability_config,
    load_fraud_model_pipeline,
    select_investigator_samples,
    validate_supported_pipeline,
    write_explainability_outputs,
    write_explainability_report,
    write_investigator_packets,
)
from src.models.train_fraud_baseline import create_model_pipeline


def _config() -> dict:
    config = deepcopy(load_explainability_config())
    config.update(
        {
            "top_local_positive_count": 2,
            "top_local_negative_count": 2,
            "minimum_absolute_contribution": 0.0,
            "probability_reconstruction_tolerance": 1e-10,
            "contribution_reconstruction_tolerance": 1e-10,
            "explanation_sample_size": 4,
        }
    )
    return config


def _training_data() -> pd.DataFrame:
    index = np.arange(24)
    return pd.DataFrame(
        {
            "transaction_id": [f"TXN-{value:03d}" for value in index],
            "customer_id": [f"CUST-{value % 4:03d}" for value in index],
            "account_id": [f"ACC-{value % 6:03d}" for value in index],
            "transaction_timestamp": pd.date_range("2025-01-01", periods=24, freq="h"),
            "amount": 10.0 + index * 4,
            "transaction_velocity_score": (index % 5) / 2,
            "channel": np.where(index % 2 == 0, "Mobile App", "ATM"),
            "fraud_label": (index % 4 == 0).astype(int),
        }
    )


def _pipeline_and_inputs():
    data = _training_data()
    features = ["amount", "transaction_velocity_score", "channel"]
    model_config = {
        "class_weight": "balanced",
        "max_iterations": 500,
        "random_state": 42,
    }
    pipeline = create_model_pipeline(
        ["amount", "transaction_velocity_score"], ["channel"], model_config
    )
    pipeline.fit(data[features], data["fraud_label"])
    test = data.iloc[-6:].copy()
    probability = pipeline.predict_proba(test[features])[:, 1]
    predicted = (probability >= 0.5).astype(int)
    actual = test["fraud_label"].to_numpy()
    error_map = {
        (1, 1): "true_positive",
        (0, 1): "false_positive",
        (0, 0): "true_negative",
        (1, 0): "false_negative",
    }
    predictions = pd.DataFrame(
        {
            "transaction_id": test["transaction_id"],
            "transaction_timestamp": test["transaction_timestamp"].astype(str),
            "actual_fraud_label": actual,
            "predicted_fraud_label": predicted,
            "fraud_probability": probability,
            "selected_threshold": 0.5,
            "error_type": [
                error_map[(int(a), int(p))]
                for a, p in zip(actual, predicted, strict=True)
            ],
        }
    )
    dictionary = pd.DataFrame(
        {
            "feature_name": features,
            "category": ["monetary", "velocity", "behavioural"],
            "description": ["Amount", "Velocity", "Channel"],
        }
    )
    mapping = identify_transformed_features(pipeline, features, dictionary)
    return pipeline, data, predictions, features, mapping


def test_explainability_configuration_and_persisted_pipeline_load(tmp_path: Path) -> None:
    assert load_explainability_config()["reason_code_prefix"] == "FRC"
    pipeline, *_ = _pipeline_and_inputs()
    path = tmp_path / "model.joblib"
    joblib.dump(pipeline, path)

    loaded = load_fraud_model_pipeline(path)
    assert isinstance(loaded.named_steps["classifier"], LogisticRegression)


def test_transformed_names_and_coefficients_align() -> None:
    pipeline, _, _, _, mapping = _pipeline_and_inputs()
    coefficients = extract_logistic_coefficients(pipeline, mapping)

    assert len(mapping) == len(pipeline.named_steps["preprocessor"].get_feature_names_out())
    assert len(coefficients) == pipeline.named_steps["classifier"].coef_.shape[1]
    assert set(mapping["source_feature_name"]) == {
        "amount",
        "transaction_velocity_score",
        "channel",
    }


def test_global_importance_contains_required_columns() -> None:
    pipeline, _, _, _, mapping = _pipeline_and_inputs()
    coefficients = extract_logistic_coefficients(pipeline, mapping)
    global_importance = calculate_global_feature_importance(coefficients)
    source_importance = aggregate_global_source_importance(global_importance)

    assert list(global_importance.columns) == GLOBAL_COLUMNS
    assert global_importance["rank"].is_monotonic_increasing
    assert set(source_importance["source_feature_name"]) == set(mapping["source_feature_name"])


def test_local_contributions_reconstruct_scores_and_probabilities() -> None:
    pipeline, data, predictions, features, mapping = _pipeline_and_inputs()
    local, contributions, reasons, quality = calculate_local_explanations(
        pipeline, data, predictions, features, mapping, _config()
    )

    assert quality["overall_status"] == "passed"
    assert quality["explanations_failed"] == 0
    assert local["decision_score_difference"].max() <= 1e-10
    assert local["probability_difference"].max() <= 1e-10
    assert np.isfinite(contributions["contribution"]).all()
    assert list(contributions.columns) == CONTRIBUTION_COLUMNS
    assert not reasons.empty


def test_contribution_rankings_and_outputs_are_deterministic() -> None:
    pipeline, data, predictions, features, mapping = _pipeline_and_inputs()
    first = calculate_local_explanations(
        pipeline, data, predictions, features, mapping, _config()
    )
    second = calculate_local_explanations(
        pipeline, data, predictions, features, mapping, _config()
    )

    pd.testing.assert_frame_equal(first[0], second[0])
    pd.testing.assert_frame_equal(first[1], second[1])
    pd.testing.assert_frame_equal(first[2], second[2])


def test_reason_codes_are_valid_safe_and_directionally_separated() -> None:
    pipeline, data, predictions, features, mapping = _pipeline_and_inputs()
    local, _, reasons, quality = calculate_local_explanations(
        pipeline, data, predictions, features, mapping, _config()
    )

    assert set(reasons["source_feature_name"]) <= set(features)
    assert not (set(reasons["source_feature_name"]) & EXCLUDED_FEATURES)
    assert quality["excluded_feature_violations"] == []
    assert reasons.query("reason_direction == 'positive'")["contribution"].gt(0).all()
    assert reasons.query("reason_direction == 'negative'")["contribution"].lt(0).all()
    assert local["positive_reasons_json"].map(json.loads).notna().all()
    assert local["negative_reasons_json"].map(json.loads).notna().all()
    assert local["explanation_evidence_json"].map(json.loads).notna().all()


def test_empty_error_type_groups_are_handled() -> None:
    pipeline, data, predictions, features, mapping = _pipeline_and_inputs()
    local, contributions, reasons, _ = calculate_local_explanations(
        pipeline, data, predictions, features, mapping, _config()
    )
    analysis = build_error_type_analysis(local, contributions, reasons)

    assert set(analysis["error_type"]) == {
        "true_positive",
        "false_positive",
        "true_negative",
        "false_negative",
    }
    assert len(analysis) == 4


def test_investigator_packets_are_generated(tmp_path: Path) -> None:
    pipeline, data, predictions, features, mapping = _pipeline_and_inputs()
    local, _, _, _ = calculate_local_explanations(
        pipeline, data, predictions, features, mapping, _config()
    )
    samples = select_investigator_samples(local, 4)
    paths = write_investigator_packets(samples, tmp_path, "test-model")

    assert paths
    assert all(path.exists() and "human reviewer" in path.read_text() for path in paths)


def test_all_outputs_can_be_written(tmp_path: Path) -> None:
    pipeline, data, predictions, features, mapping = _pipeline_and_inputs()
    coefficients = extract_logistic_coefficients(pipeline, mapping)
    global_importance = calculate_global_feature_importance(coefficients)
    source_importance = aggregate_global_source_importance(global_importance)
    local, contributions, reasons, quality = calculate_local_explanations(
        pipeline, data, predictions, features, mapping, _config()
    )
    errors = build_error_type_analysis(local, contributions, reasons)
    summary = build_explainability_summary(
        {"model_version": "test", "model_type": "LogisticRegression"},
        global_importance,
        source_importance,
        local,
        reasons,
        quality,
        errors,
        len(predictions),
        3,
    )
    config = _config()
    for key in (
        "coefficient_output_path",
        "source_importance_output_path",
        "local_explanation_output_path",
        "contribution_output_path",
        "reason_code_output_path",
        "quality_output_path",
        "error_type_output_path",
        "summary_output_path",
    ):
        config[key] = str(tmp_path / "outputs" / Path(config[key]).name)
    paths = write_explainability_outputs(
        global_importance,
        source_importance,
        local,
        contributions,
        reasons,
        quality,
        errors,
        summary,
        config,
    )
    report_path = tmp_path / "reports" / "explainability.md"
    write_explainability_report(summary, report_path)

    assert all(path.exists() and path.stat().st_size > 0 for path in paths.values())
    assert report_path.exists()


def test_unsupported_pipeline_raises_clear_error() -> None:
    unsupported = Pipeline([("scaler", StandardScaler())])
    with pytest.raises(ValueError, match="preprocessor and classifier"):
        validate_supported_pipeline(unsupported)
