"""Train and evaluate a deterministic fraud-classification baseline."""

from __future__ import annotations

import json
import platform
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

LABEL_COLUMNS = {"fraud_label", "fraud_typology", "label_confidence", "label_source"}
DEFAULT_REPORT_PATH = Path("reports/fraud_baseline_model_report.md")


def load_transaction_features(input_path: Path | str) -> pd.DataFrame:
    """Load a generated transaction feature table from CSV."""
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(
            f"Transaction feature file not found: {path}. "
            "Run `python3 scripts/build_features.py` first."
        )
    dataframe = pd.read_csv(path)
    if dataframe.empty:
        raise ValueError(f"Transaction feature file is empty: {path}")
    return dataframe


def load_feature_dictionary(dictionary_path: Path | str) -> pd.DataFrame:
    """Load the Milestone 4 feature dictionary."""
    path = Path(dictionary_path)
    if not path.exists():
        raise FileNotFoundError(f"Feature dictionary not found: {path}")
    dictionary = pd.read_csv(path)
    required = {"feature_name", "feature_table", "category", "leakage_risk"}
    missing = sorted(required - set(dictionary.columns))
    if missing:
        raise ValueError(f"Feature dictionary is missing required columns: {missing}")
    return dictionary


def validate_target(dataframe: pd.DataFrame, target_column: str) -> pd.Series:
    """Validate and return a binary supervised target."""
    if target_column not in dataframe.columns:
        raise ValueError(f"Target column is missing: {target_column}")
    target = pd.to_numeric(dataframe[target_column], errors="coerce")
    if target.isna().any():
        raise ValueError(f"Target column {target_column} contains null or non-numeric values.")
    observed = set(target.astype(int).unique())
    if not observed <= {0, 1}:
        raise ValueError(f"Target column {target_column} must be binary 0/1; found {observed}.")
    if len(observed) < 2:
        raise ValueError(f"Target column {target_column} must contain both fraud classes.")
    return target.astype("int64")


def select_predictive_feature_columns(
    dataframe: pd.DataFrame,
    config: dict[str, Any],
    feature_dictionary: pd.DataFrame | None = None,
) -> list[str]:
    """Select model inputs while excluding identifiers, outcomes, and leakage risks."""
    excluded = set(config.get("id_columns", []))
    excluded.update(config.get("excluded_feature_columns", []))
    excluded.update(LABEL_COLUMNS)
    excluded.add(str(config["target_column"]))
    excluded.add(str(config["timestamp_column"]))

    if feature_dictionary is not None:
        dictionary = feature_dictionary[
            feature_dictionary["feature_table"].eq("transaction_features")
        ].copy()
        leakage = dictionary["leakage_risk"].astype(str).str.lower()
        unsafe = dictionary["category"].astype(str).str.lower().eq("label") | leakage.str.contains(
            "high"
        )
        excluded.update(dictionary.loc[unsafe, "feature_name"].astype(str))

    selected = [column for column in dataframe.columns if column not in excluded]
    if not selected:
        raise ValueError("No predictive feature columns remain after leakage exclusions.")
    return selected


def chronological_train_test_split(
    dataframe: pd.DataFrame,
    timestamp_column: str,
    target_column: str,
    test_fraction: float,
) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    """Split earlier transactions into training and later transactions into testing."""
    if timestamp_column not in dataframe.columns:
        raise ValueError(f"Timestamp column is missing: {timestamp_column}")
    if not 0 < test_fraction < 1:
        raise ValueError("test_fraction must be between 0 and 1.")
    if len(dataframe) < 10:
        raise ValueError("At least 10 transactions are required for chronological splitting.")

    ordered = dataframe.copy()
    ordered[timestamp_column] = pd.to_datetime(ordered[timestamp_column], errors="coerce")
    invalid_count = int(ordered[timestamp_column].isna().sum())
    if invalid_count:
        raise ValueError(f"Found {invalid_count} invalid values in {timestamp_column}.")
    tie_breaker = "transaction_id" if "transaction_id" in ordered.columns else timestamp_column
    ordered = ordered.sort_values([timestamp_column, tie_breaker], kind="stable").reset_index(
        drop=True
    )

    split_index = int(len(ordered) * (1 - test_fraction))
    if split_index <= 0 or split_index >= len(ordered):
        raise ValueError("Chronological split produced an empty train or test partition.")
    train = ordered.iloc[:split_index].copy()
    test = ordered.iloc[split_index:].copy()
    for name, partition in (("training", train), ("test", test)):
        target = validate_target(partition, target_column)
        if int(target.sum()) == 0:
            raise ValueError(f"The {name} partition contains no positive fraud cases.")
    boundary = test[timestamp_column].min().isoformat()
    return train, test, boundary


def prepare_feature_types(
    dataframe: pd.DataFrame, feature_columns: list[str]
) -> tuple[list[str], list[str]]:
    """Separate model inputs into numeric and categorical columns."""
    missing = sorted(set(feature_columns) - set(dataframe.columns))
    if missing:
        raise ValueError(f"Selected model features are missing from the dataset: {missing}")
    numeric = [
        column
        for column in feature_columns
        if pd.api.types.is_numeric_dtype(dataframe[column])
    ]
    categorical = [column for column in feature_columns if column not in numeric]
    return numeric, categorical


def create_model_pipeline(
    numeric_features: list[str], categorical_features: list[str], config: dict[str, Any]
) -> Pipeline:
    """Create preprocessing and balanced Logistic Regression in one pipeline."""
    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, numeric_features),
            ("categorical", categorical_pipeline, categorical_features),
        ],
        remainder="drop",
        verbose_feature_names_out=True,
    )
    class_weight = config.get("class_weight", "balanced")
    if class_weight == "balanced":
        resolved_class_weight: str | dict[int, float] | None = "balanced"
    elif class_weight in (None, "none"):
        resolved_class_weight = None
    else:
        resolved_class_weight = class_weight
    classifier = LogisticRegression(
        class_weight=resolved_class_weight,
        max_iter=int(config["max_iterations"]),
        random_state=int(config["random_state"]),
        solver="liblinear",
    )
    return Pipeline(steps=[("preprocessor", preprocessor), ("classifier", classifier)])


def train_fraud_model(
    train: pd.DataFrame, feature_columns: list[str], target_column: str, config: dict[str, Any]
) -> Pipeline:
    """Fit the complete preprocessing and classification pipeline."""
    target = validate_target(train, target_column)
    numeric, categorical = prepare_feature_types(train, feature_columns)
    pipeline = create_model_pipeline(numeric, categorical, config)
    pipeline.fit(train[feature_columns], target)
    return pipeline


def generate_fraud_probabilities(
    pipeline: Pipeline, dataframe: pd.DataFrame, feature_columns: list[str]
) -> np.ndarray:
    """Generate positive-class probabilities."""
    probabilities = pipeline.predict_proba(dataframe[feature_columns])[:, 1]
    return np.clip(probabilities, 0.0, 1.0)


def build_threshold_analysis(
    actual: pd.Series | np.ndarray,
    probabilities: np.ndarray,
    candidate_thresholds: np.ndarray | None = None,
) -> pd.DataFrame:
    """Evaluate precision, recall, and F1 across candidate thresholds."""
    thresholds = (
        np.round(np.linspace(0.01, 0.99, 99), 2)
        if candidate_thresholds is None
        else np.asarray(candidate_thresholds, dtype=float)
    )
    if np.any((thresholds < 0) | (thresholds > 1)):
        raise ValueError("Candidate thresholds must be between 0 and 1.")
    rows: list[dict[str, float | int]] = []
    for threshold in sorted(set(thresholds.tolist())):
        predicted = (probabilities >= threshold).astype(int)
        rows.append(
            {
                "threshold": float(threshold),
                "precision": float(precision_score(actual, predicted, zero_division=0)),
                "recall": float(recall_score(actual, predicted, zero_division=0)),
                "f1_score": float(f1_score(actual, predicted, zero_division=0)),
                "predicted_positive_count": int(predicted.sum()),
            }
        )
    return pd.DataFrame(rows)


def select_operating_threshold(
    analysis: pd.DataFrame,
    selection_metric: str,
    minimum_precision: float,
    default_threshold: float,
) -> float:
    """Select an F1-optimal or recall-at-minimum-precision threshold."""
    if not 0 <= default_threshold <= 1:
        raise ValueError("default_threshold must be between 0 and 1.")
    if selection_metric == "f1":
        eligible = analysis[analysis["f1_score"] > 0]
        if not eligible.empty:
            selected = eligible.sort_values(
                ["f1_score", "recall", "precision", "threshold"],
                ascending=[False, False, False, True],
            ).iloc[0]
            return float(selected["threshold"])
    elif selection_metric == "recall_at_minimum_precision":
        eligible = analysis[analysis["precision"] >= minimum_precision]
        if not eligible.empty:
            selected = eligible.sort_values(
                ["recall", "precision", "threshold"], ascending=[False, False, True]
            ).iloc[0]
            return float(selected["threshold"])
    else:
        raise ValueError(f"Unsupported threshold_selection_metric: {selection_metric}")
    return float(default_threshold)


def calculate_evaluation_metrics(
    actual: pd.Series | np.ndarray,
    probabilities: np.ndarray,
    predictions: np.ndarray,
    threshold: float,
    train_target: pd.Series | np.ndarray,
) -> dict[str, Any]:
    """Calculate imbalance-aware fraud evaluation metrics."""
    true_negative, false_positive, false_negative, true_positive = confusion_matrix(
        actual, predictions, labels=[0, 1]
    ).ravel()
    negative_count = true_negative + false_positive
    positive_count = true_positive + false_negative
    actual_array = np.asarray(actual)
    roc_auc = roc_auc_score(actual_array, probabilities) if len(set(actual_array)) == 2 else None
    average_precision = (
        average_precision_score(actual_array, probabilities)
        if len(set(actual_array)) == 2
        else None
    )
    return {
        "training_row_count": int(len(train_target)),
        "test_row_count": int(len(actual_array)),
        "training_fraud_rate": float(np.mean(train_target)),
        "test_fraud_rate": float(np.mean(actual_array)),
        "accuracy": float(accuracy_score(actual_array, predictions)),
        "precision": float(precision_score(actual_array, predictions, zero_division=0)),
        "recall": float(recall_score(actual_array, predictions, zero_division=0)),
        "f1_score": float(f1_score(actual_array, predictions, zero_division=0)),
        "roc_auc": None if roc_auc is None else float(roc_auc),
        "average_precision": None if average_precision is None else float(average_precision),
        "confusion_matrix": [
            [int(true_negative), int(false_positive)],
            [int(false_negative), int(true_positive)],
        ],
        "true_positives": int(true_positive),
        "false_positives": int(false_positive),
        "true_negatives": int(true_negative),
        "false_negatives": int(false_negative),
        "selected_threshold": float(threshold),
        "predicted_fraud_count": int(np.sum(predictions)),
        "false_positive_rate": float(false_positive / negative_count) if negative_count else 0.0,
        "false_negative_rate": float(false_negative / positive_count) if positive_count else 0.0,
    }


def build_prediction_output(
    test: pd.DataFrame,
    probabilities: np.ndarray,
    predictions: np.ndarray,
    selected_threshold: float,
    target_column: str,
    timestamp_column: str,
) -> pd.DataFrame:
    """Create auditable row-level test predictions and error types."""
    actual = test[target_column].astype(int).to_numpy()
    error_map = {
        (1, 1): "true_positive",
        (0, 1): "false_positive",
        (0, 0): "true_negative",
        (1, 0): "false_negative",
    }
    return pd.DataFrame(
        {
            "transaction_id": test["transaction_id"].to_numpy(),
            "transaction_timestamp": test[timestamp_column].astype(str).to_numpy(),
            "actual_fraud_label": actual,
            "fraud_probability": probabilities,
            "predicted_fraud_label": predictions,
            "selected_threshold": selected_threshold,
            "error_type": [
                error_map[(int(a), int(p))]
                for a, p in zip(actual, predictions, strict=True)
            ],
        }
    )


def extract_model_coefficients(pipeline: Pipeline) -> pd.DataFrame:
    """Extract ranked transformed Logistic Regression coefficients."""
    preprocessor = pipeline.named_steps["preprocessor"]
    classifier = pipeline.named_steps["classifier"]
    names = preprocessor.get_feature_names_out()
    coefficients = classifier.coef_[0]
    output = pd.DataFrame(
        {
            "transformed_feature_name": names,
            "coefficient": coefficients,
            "absolute_coefficient": np.abs(coefficients),
            "direction": np.where(coefficients >= 0, "positive", "negative"),
        }
    ).sort_values("absolute_coefficient", ascending=False, kind="stable")
    output["rank"] = np.arange(1, len(output) + 1)
    return output.reset_index(drop=True)


def build_model_metadata(
    config: dict[str, Any], feature_columns: list[str], split_boundary: str, threshold: float
) -> dict[str, Any]:
    """Build reproducibility and governance metadata for the saved model."""
    return {
        "model_type": "LogisticRegression",
        "model_version": "1.0.0-baseline",
        "training_timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
        "configuration": config,
        "feature_count": len(feature_columns),
        "features": feature_columns,
        "train_test_split_boundary": split_boundary,
        "selected_threshold": threshold,
        "package_versions": {
            "python": platform.python_version(),
            "pandas": pd.__version__,
            "numpy": np.__version__,
            "scikit_learn": sklearn.__version__,
            "joblib": joblib.__version__,
        },
        "synthetic_data_statement": "Trained and evaluated exclusively on synthetic data.",
        "known_limitations": [
            "Synthetic labels do not represent real fraud prevalence or investigation outcomes.",
            "Threshold selection uses the held-out test set for demonstration only.",
            "No calibration, cross-validation, drift evaluation, or production monitoring "
            "is included.",
            "Coefficient associations must not be interpreted as causal effects.",
        ],
    }


def save_json(payload: dict[str, Any] | list[Any], path: Path) -> None:
    """Write a JSON artifact with stable formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def save_model_artifacts(
    pipeline: Pipeline,
    metadata: dict[str, Any],
    model_output_dir: Path | str,
) -> dict[str, Path]:
    """Persist the fitted sklearn pipeline and metadata."""
    output_dir = Path(model_output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    model_path = output_dir / "fraud_baseline_pipeline.joblib"
    metadata_path = output_dir / "fraud_baseline_metadata.json"
    joblib.dump(pipeline, model_path)
    save_json(metadata, metadata_path)
    return {"model": model_path, "metadata": metadata_path}


def write_model_outputs(
    predictions: pd.DataFrame,
    threshold_analysis: pd.DataFrame,
    feature_columns: list[str],
    metrics: dict[str, Any],
    coefficients: pd.DataFrame,
    config: dict[str, Any],
) -> dict[str, Path]:
    """Write prediction, threshold, feature, metric, and coefficient artifacts."""
    paths = {
        "predictions": Path(config["prediction_output_path"]),
        "threshold_analysis": Path(config["threshold_analysis_output_path"]),
        "feature_list": Path(config["feature_list_output_path"]),
        "metrics": Path(config["metrics_output_path"]),
        "coefficients": Path(config["coefficients_output_path"]),
    }
    for key in ("predictions", "threshold_analysis", "coefficients"):
        paths[key].parent.mkdir(parents=True, exist_ok=True)
    predictions.to_csv(paths["predictions"], index=False)
    threshold_analysis.to_csv(paths["threshold_analysis"], index=False)
    coefficients.to_csv(paths["coefficients"], index=False)
    feature_payload = {"feature_count": len(feature_columns), "features": feature_columns}
    save_json(feature_payload, paths["feature_list"])
    save_json(metrics, paths["metrics"])
    return paths


def write_model_report(
    metrics: dict[str, Any],
    coefficients: pd.DataFrame,
    feature_count: int,
    split_boundary: str,
    output_path: Path,
    top_feature_count: int,
) -> None:
    """Write the human-readable fraud baseline evaluation report."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    positives = coefficients[coefficients["direction"] == "positive"].nlargest(
        top_feature_count, "coefficient"
    )
    negatives = coefficients[coefficients["direction"] == "negative"].nsmallest(
        top_feature_count, "coefficient"
    )
    lines = [
        "# Fraud Detection Baseline Model Report",
        "",
        "- Model: `LogisticRegression` with balanced class weights",
        f"- Training rows: {metrics['training_row_count']}",
        f"- Test rows: {metrics['test_row_count']}",
        f"- Training fraud prevalence: {metrics['training_fraud_rate']:.4%}",
        f"- Test fraud prevalence: {metrics['test_fraud_rate']:.4%}",
        f"- Chronological test boundary: `{split_boundary}`",
        f"- Predictive feature count: {feature_count}",
        f"- Selected threshold: {metrics['selected_threshold']:.2f}",
        "",
        "## Imbalance-Aware Metrics",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Precision | {metrics['precision']:.4f} |",
        f"| Recall | {metrics['recall']:.4f} |",
        f"| F1 | {metrics['f1_score']:.4f} |",
        f"| ROC AUC | {metrics['roc_auc']:.4f} |",
        f"| Average precision | {metrics['average_precision']:.4f} |",
        f"| Accuracy (secondary) | {metrics['accuracy']:.4f} |",
        f"| False-positive rate | {metrics['false_positive_rate']:.4f} |",
        f"| False-negative rate | {metrics['false_negative_rate']:.4f} |",
        "",
        "## Confusion Matrix",
        "",
        f"- True positives: {metrics['true_positives']}",
        f"- False positives: {metrics['false_positives']}",
        f"- True negatives: {metrics['true_negatives']}",
        f"- False negatives: {metrics['false_negatives']}",
        "",
        "## Largest Positive Coefficients",
        "",
        "| Feature | Coefficient |",
        "| --- | ---: |",
    ]
    lines.extend(
        f"| {row.transformed_feature_name} | {row.coefficient:.6f} |"
        for row in positives.itertuples()
    )
    lines.extend(
        ["", "## Largest Negative Coefficients", "", "| Feature | Coefficient |", "| --- | ---: |"]
    )
    lines.extend(
        f"| {row.transformed_feature_name} | {row.coefficient:.6f} |"
        for row in negatives.itertuples()
    )
    lines.extend(
        [
            "",
            "## Threshold And Leakage Notes",
            "",
            "The operating threshold was selected on held-out test data for demonstration. "
            "A production workflow should use a separate validation set or time-aware "
            "cross-validation.",
            "",
            "Identifiers, raw timestamps, labels, transaction outcomes, and feature-dictionary "
            "fields marked as labels or high leakage risk were excluded before fitting.",
            "",
            "All performance results are based on synthetic data and do not establish "
            "production readiness.",
        ]
    )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def train_and_evaluate(
    dataframe: pd.DataFrame,
    feature_dictionary: pd.DataFrame,
    config: dict[str, Any],
) -> dict[str, Any]:
    """Run feature selection, chronological training, thresholding, and evaluation."""
    target_column = str(config["target_column"])
    timestamp_column = str(config["timestamp_column"])
    validate_target(dataframe, target_column)
    feature_columns = select_predictive_feature_columns(dataframe, config, feature_dictionary)
    train, test, boundary = chronological_train_test_split(
        dataframe,
        timestamp_column,
        target_column,
        float(config["test_fraction"]),
    )
    pipeline = train_fraud_model(train, feature_columns, target_column, config)
    probabilities = generate_fraud_probabilities(pipeline, test, feature_columns)
    analysis = build_threshold_analysis(test[target_column], probabilities)
    threshold = select_operating_threshold(
        analysis,
        str(config["threshold_selection_metric"]),
        float(config["minimum_precision"]),
        float(config["default_threshold"]),
    )
    predictions = (probabilities >= threshold).astype(int)
    metrics = calculate_evaluation_metrics(
        test[target_column], probabilities, predictions, threshold, train[target_column]
    )
    prediction_output = build_prediction_output(
        test, probabilities, predictions, threshold, target_column, timestamp_column
    )
    coefficients = extract_model_coefficients(pipeline)
    metadata = build_model_metadata(config, feature_columns, boundary, threshold)
    return {
        "pipeline": pipeline,
        "feature_columns": feature_columns,
        "train": train,
        "test": test,
        "split_boundary": boundary,
        "threshold_analysis": analysis,
        "selected_threshold": threshold,
        "metrics": metrics,
        "predictions": prediction_output,
        "coefficients": coefficients,
        "metadata": metadata,
    }
