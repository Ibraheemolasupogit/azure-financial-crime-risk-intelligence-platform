"""Native Logistic Regression explanations for the synthetic fraud baseline."""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import yaml
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

EXCLUDED_FEATURES = {
    "transaction_id",
    "account_id",
    "customer_id",
    "device_id",
    "session_id",
    "transaction_timestamp",
    "fraud_label",
    "fraud_typology",
    "label_confidence",
    "label_source",
    "actual_fraud_label",
    "transaction_status",
}

GLOBAL_COLUMNS = [
    "transformed_feature_name",
    "source_feature_name",
    "coefficient",
    "absolute_coefficient",
    "direction",
    "rank",
    "feature_category",
    "interpretation",
    "caveat",
]

CONTRIBUTION_COLUMNS = [
    "transaction_id",
    "transformed_feature_name",
    "source_feature_name",
    "transformed_feature_value",
    "coefficient",
    "contribution",
    "contribution_direction",
    "absolute_contribution",
    "contribution_rank",
    "included_in_reason_codes",
    "feature_category",
]

REASON_COLUMNS = [
    "transaction_id",
    "reason_code",
    "reason_rank",
    "reason_direction",
    "source_feature_name",
    "observed_value",
    "contribution",
    "human_readable_reason",
    "threshold_context",
    "caveat",
]


def load_explainability_config(
    config_path: Path | str = "configs/explainability_config.yaml",
) -> dict[str, Any]:
    """Load deterministic explainability settings."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Explainability configuration not found: {path}")
    with path.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)
    if not isinstance(config, dict):
        raise ValueError(f"Explainability configuration must be a mapping: {path}")
    for key in (
        "top_local_positive_count",
        "top_local_negative_count",
        "probability_reconstruction_tolerance",
        "contribution_reconstruction_tolerance",
    ):
        if float(config[key]) < 0:
            raise ValueError(f"Explainability setting cannot be negative: {key}")
    return config


def load_fraud_model_pipeline(model_path: Path | str) -> Pipeline:
    """Load and validate the persisted sklearn Logistic Regression pipeline."""
    path = Path(model_path)
    if not path.exists():
        raise FileNotFoundError(f"Fraud model pipeline not found: {path}")
    pipeline = joblib.load(path)
    validate_supported_pipeline(pipeline)
    return pipeline


def validate_supported_pipeline(pipeline: Any) -> None:
    """Fail clearly when a model cannot support native linear explanations."""
    if not isinstance(pipeline, Pipeline):
        raise ValueError("Explainability requires a fitted sklearn Pipeline.")
    if "preprocessor" not in pipeline.named_steps or "classifier" not in pipeline.named_steps:
        raise ValueError("Pipeline must contain preprocessor and classifier steps.")
    if not isinstance(pipeline.named_steps["classifier"], LogisticRegression):
        raise ValueError("Only LogisticRegression classifiers are supported in Milestone 8.")
    classifier = pipeline.named_steps["classifier"]
    if not hasattr(classifier, "coef_"):
        raise ValueError("LogisticRegression classifier is not fitted.")


def _load_csv(path: Path | str, name: str) -> pd.DataFrame:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Required {name} file not found: {file_path}")
    dataframe = pd.read_csv(file_path)
    if dataframe.empty:
        raise ValueError(f"Required {name} file is empty: {file_path}")
    return dataframe


def load_transaction_feature_data(path: Path | str) -> pd.DataFrame:
    """Load transaction features used by the persisted model."""
    dataframe = _load_csv(path, "transaction features")
    required = {"transaction_id", "customer_id", "account_id", "transaction_timestamp"}
    missing = sorted(required - set(dataframe.columns))
    if missing:
        raise ValueError(f"Transaction features are missing required columns: {missing}")
    return dataframe


def load_fraud_test_predictions(path: Path | str) -> pd.DataFrame:
    """Load row-level held-out predictions and outcome classifications."""
    dataframe = _load_csv(path, "fraud test predictions")
    required = {
        "transaction_id",
        "actual_fraud_label",
        "predicted_fraud_label",
        "fraud_probability",
        "selected_threshold",
        "error_type",
    }
    missing = sorted(required - set(dataframe.columns))
    if missing:
        raise ValueError(f"Fraud predictions are missing required columns: {missing}")
    return dataframe


def load_final_model_feature_list(path: Path | str) -> list[str]:
    """Load the exact source feature list persisted during model training."""
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Model feature list not found: {file_path}")
    payload = json.loads(file_path.read_text(encoding="utf-8"))
    features = payload.get("features")
    if not isinstance(features, list) or not features:
        raise ValueError("Model feature list must contain a non-empty features array.")
    prohibited = sorted(set(features) & EXCLUDED_FEATURES)
    if prohibited:
        raise ValueError(f"Excluded identifier or label features found in model list: {prohibited}")
    return [str(feature) for feature in features]


def identify_transformed_features(
    pipeline: Pipeline,
    source_features: list[str],
    feature_dictionary: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Map transformed numeric and one-hot columns to their source features."""
    validate_supported_pipeline(pipeline)
    names = pipeline.named_steps["preprocessor"].get_feature_names_out().tolist()
    sorted_sources = sorted(source_features, key=len, reverse=True)
    category_map: dict[str, str] = {}
    description_map: dict[str, str] = {}
    if feature_dictionary is not None and not feature_dictionary.empty:
        for row in feature_dictionary.itertuples():
            category_map[str(row.feature_name)] = str(row.category)
            description_map[str(row.feature_name)] = str(row.description)

    rows = []
    for transformed_name in names:
        suffix = transformed_name.split("__", 1)[-1]
        source = next(
            (
                candidate
                for candidate in sorted_sources
                if suffix == candidate or suffix.startswith(f"{candidate}_")
            ),
            None,
        )
        if source is None:
            raise ValueError(
                f"Cannot map transformed feature to a source feature: {transformed_name}"
            )
        rows.append(
            {
                "transformed_feature_name": transformed_name,
                "source_feature_name": source,
                "feature_category": category_map.get(source, "uncategorised"),
                "source_description": description_map.get(source, source.replace("_", " ")),
                "transform_type": (
                    "categorical"
                    if transformed_name.startswith("categorical__")
                    else "numeric"
                ),
            }
        )
    mapping = pd.DataFrame(rows)
    prohibited = sorted(set(mapping["source_feature_name"]) & EXCLUDED_FEATURES)
    if prohibited:
        raise ValueError(f"Excluded features found in transformed model inputs: {prohibited}")
    return mapping


def extract_logistic_coefficients(
    pipeline: Pipeline, transformed_mapping: pd.DataFrame
) -> pd.DataFrame:
    """Extract coefficients aligned to transformed feature names."""
    classifier = pipeline.named_steps["classifier"]
    coefficients = classifier.coef_[0]
    if len(coefficients) != len(transformed_mapping):
        raise ValueError("Coefficient count does not match transformed feature count.")
    output = transformed_mapping.copy()
    output["coefficient"] = coefficients
    output["absolute_coefficient"] = np.abs(coefficients)
    output["direction"] = np.where(coefficients >= 0, "positive", "negative")
    return output


def calculate_global_feature_importance(coefficients: pd.DataFrame) -> pd.DataFrame:
    """Create ranked transformed-feature association output."""
    output = coefficients.copy().sort_values(
        ["absolute_coefficient", "transformed_feature_name"],
        ascending=[False, True],
        kind="stable",
    )
    output["rank"] = np.arange(1, len(output) + 1)
    output["interpretation"] = output.apply(
        lambda row: (
            "Higher transformed values are associated with "
            f"{'higher' if row.coefficient >= 0 else 'lower'} model log-odds."
        ),
        axis=1,
    )
    output["caveat"] = "Association in this synthetic model; not causal evidence."
    return output[GLOBAL_COLUMNS].reset_index(drop=True)


def aggregate_global_source_importance(global_importance: pd.DataFrame) -> pd.DataFrame:
    """Aggregate one-hot levels and numeric terms to source-feature associations."""
    grouped = global_importance.groupby("source_feature_name", sort=True)
    output = grouped.agg(
        aggregate_absolute_importance=("absolute_coefficient", "sum"),
        maximum_absolute_coefficient=("absolute_coefficient", "max"),
        positive_level_count=("coefficient", lambda values: int((values > 0).sum())),
        negative_level_count=("coefficient", lambda values: int((values < 0).sum())),
        transformed_feature_count=("transformed_feature_name", "count"),
    ).reset_index()
    output = output.sort_values(
        ["aggregate_absolute_importance", "source_feature_name"],
        ascending=[False, True],
        kind="stable",
    ).reset_index(drop=True)
    output["rank"] = np.arange(1, len(output) + 1)
    output["interpretation"] = output.apply(
        lambda row: (
            f"{int(row.transformed_feature_count)} transformed term(s) contribute to this "
            "source-feature association."
        ),
        axis=1,
    )
    return output


def _reason_code(prefix: str, source: str, direction: str) -> str:
    token = re.sub(r"[^A-Z0-9]+", "_", source.upper()).strip("_")
    return f"{prefix}_{token}_{'UP' if direction == 'positive' else 'DOWN'}"


def _human_reason(source: str, observed: Any, direction: str) -> str:
    phrase = source.replace("_", " ")
    movement = "increased" if direction == "positive" else "reduced"
    return f"Observed {phrase}={observed!s} {movement} the model decision score."


def _sigmoid(value: float) -> float:
    if value >= 0:
        return 1.0 / (1.0 + math.exp(-value))
    exponential = math.exp(value)
    return exponential / (1.0 + exponential)


def calculate_local_explanations(
    pipeline: Pipeline,
    transaction_features: pd.DataFrame,
    predictions: pd.DataFrame,
    feature_list: list[str],
    transformed_mapping: pd.DataFrame,
    config: dict[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Calculate per-transaction contributions, reasons, and reconstruction quality."""
    context_columns = [
        "transaction_id",
        "customer_id",
        "account_id",
        *feature_list,
    ]
    context_columns = list(dict.fromkeys(context_columns))
    missing = sorted(set(context_columns) - set(transaction_features.columns))
    if missing:
        raise ValueError(f"Transaction features are missing model inputs: {missing}")
    data = predictions.merge(
        transaction_features[context_columns],
        on="transaction_id",
        how="left",
        validate="one_to_one",
    )
    if data[feature_list].isna().all(axis=1).any():
        raise ValueError("One or more predictions have no matching transformed feature vector.")

    allowed_error_types = set()
    if config["include_false_positives"]:
        allowed_error_types.add("false_positive")
    if config["include_false_negatives"]:
        allowed_error_types.add("false_negative")
    if config["include_true_positives"] or config["include_correct_predictions"]:
        allowed_error_types.add("true_positive")
    if config["include_true_negatives"] or config["include_correct_predictions"]:
        allowed_error_types.add("true_negative")
    data = data[data["error_type"].isin(allowed_error_types)].reset_index(drop=True)
    if data.empty:
        raise ValueError("Explainability filters excluded every prediction row.")

    preprocessor = pipeline.named_steps["preprocessor"]
    classifier = pipeline.named_steps["classifier"]
    transformed = preprocessor.transform(data[feature_list])
    values = transformed.toarray() if hasattr(transformed, "toarray") else np.asarray(transformed)
    coefficients = classifier.coef_[0]
    intercept = float(classifier.intercept_[0])
    contributions_matrix = values * coefficients
    decision_scores = pipeline.decision_function(data[feature_list])
    model_probabilities = pipeline.predict_proba(data[feature_list])[:, 1]

    local_rows: list[dict[str, Any]] = []
    contribution_rows: list[dict[str, Any]] = []
    reason_rows: list[dict[str, Any]] = []
    invalid_reason_count = 0
    excluded_violations: set[str] = set()
    missing_feature_count = int(data[feature_list].isna().sum().sum())
    minimum = float(config["minimum_absolute_contribution"])

    for position, row in data.iterrows():
        transaction_contributions = []
        for feature_position, mapping in transformed_mapping.iterrows():
            contribution = float(contributions_matrix[position, feature_position])
            transaction_contributions.append(
                {
                    "transaction_id": row["transaction_id"],
                    "transformed_feature_name": mapping["transformed_feature_name"],
                    "source_feature_name": mapping["source_feature_name"],
                    "transformed_feature_value": float(values[position, feature_position]),
                    "coefficient": float(coefficients[feature_position]),
                    "contribution": contribution,
                    "contribution_direction": (
                        "positive"
                        if contribution > 0
                        else "negative"
                        if contribution < 0
                        else "neutral"
                    ),
                    "absolute_contribution": abs(contribution),
                    "feature_category": mapping["feature_category"],
                }
            )
        ranked = sorted(
            transaction_contributions,
            key=lambda item: (-item["absolute_contribution"], item["transformed_feature_name"]),
        )
        for rank, item in enumerate(ranked, start=1):
            item["contribution_rank"] = rank

        positive = [
            item
            for item in ranked
            if item["contribution"] > 0 and item["absolute_contribution"] >= minimum
        ][: int(config["top_local_positive_count"])]
        negative = [
            item
            for item in ranked
            if item["contribution"] < 0 and item["absolute_contribution"] >= minimum
        ][: int(config["top_local_negative_count"])]
        reason_keys = {
            (item["transformed_feature_name"], item["contribution_direction"])
            for item in positive + negative
        }
        for item in transaction_contributions:
            item["included_in_reason_codes"] = (
                item["transformed_feature_name"], item["contribution_direction"]
            ) in reason_keys
            contribution_rows.append(item)

        positive_reasons = []
        negative_reasons = []
        for direction, selected, destination in (
            ("positive", positive, positive_reasons),
            ("negative", negative, negative_reasons),
        ):
            for reason_rank, item in enumerate(selected, start=1):
                source = item["source_feature_name"]
                if source in EXCLUDED_FEATURES or source not in feature_list:
                    invalid_reason_count += 1
                    excluded_violations.add(source)
                observed = row[source]
                reason = {
                    "reason_code": _reason_code(config["reason_code_prefix"], source, direction),
                    "reason_rank": reason_rank,
                    "reason_direction": direction,
                    "source_feature_name": source,
                    "observed_value": observed,
                    "contribution": item["contribution"],
                    "human_readable_reason": _human_reason(source, observed, direction),
                    "threshold_context": (
                        f"probability={row['fraud_probability']:.6f}; "
                        f"selected_threshold={row['selected_threshold']:.6f}"
                    ),
                    "caveat": "Model association only; not causal or proof of fraud.",
                }
                destination.append(reason)
                reason_rows.append({"transaction_id": row["transaction_id"], **reason})

        contribution_sum = float(contributions_matrix[position].sum())
        reconstructed_decision = intercept + contribution_sum
        reconstructed_probability = _sigmoid(reconstructed_decision)
        decision_difference = abs(reconstructed_decision - float(decision_scores[position]))
        probability_difference = abs(
            reconstructed_probability - float(model_probabilities[position])
        )
        passed = (
            np.isfinite(contribution_sum)
            and decision_difference <= float(config["contribution_reconstruction_tolerance"])
            and probability_difference <= float(config["probability_reconstruction_tolerance"])
        )
        evidence = {
            "feature_count": len(transaction_contributions),
            "top_positive_transformed_features": [
                item["transformed_feature_name"] for item in positive
            ],
            "top_negative_transformed_features": [
                item["transformed_feature_name"] for item in negative
            ],
            "contribution_reconstruction_tolerance": float(
                config["contribution_reconstruction_tolerance"]
            ),
            "probability_reconstruction_tolerance": float(
                config["probability_reconstruction_tolerance"]
            ),
        }
        local_rows.append(
            {
                "transaction_id": row["transaction_id"],
                "customer_id": row["customer_id"],
                "account_id": row["account_id"],
                "transaction_timestamp": row["transaction_timestamp"],
                "actual_fraud_label": int(row["actual_fraud_label"]),
                "predicted_fraud_label": int(row["predicted_fraud_label"]),
                "fraud_probability": float(row["fraud_probability"]),
                "selected_threshold": float(row["selected_threshold"]),
                "error_type": row["error_type"],
                "decision_score": float(decision_scores[position]),
                "intercept": intercept,
                "contribution_sum": contribution_sum,
                "reconstructed_decision_score": reconstructed_decision,
                "reconstructed_probability": reconstructed_probability,
                "decision_score_difference": decision_difference,
                "probability_difference": probability_difference,
                "explanation_status": "passed" if passed else "failed",
                "top_positive_reason": (
                    positive_reasons[0]["human_readable_reason"] if positive_reasons else ""
                ),
                "top_negative_reason": (
                    negative_reasons[0]["human_readable_reason"] if negative_reasons else ""
                ),
                "positive_reasons_json": json.dumps(positive_reasons, sort_keys=True, default=str),
                "negative_reasons_json": json.dumps(negative_reasons, sort_keys=True, default=str),
                "explanation_evidence_json": json.dumps(evidence, sort_keys=True),
                "synthetic_data_flag": True,
            }
        )

    local = pd.DataFrame(local_rows)
    contributions = pd.DataFrame(contribution_rows, columns=CONTRIBUTION_COLUMNS)
    reasons = pd.DataFrame(reason_rows, columns=REASON_COLUMNS)
    quality = {
        "run_timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
        "transactions_explained": int(len(local)),
        "explanations_passed": int(local["explanation_status"].eq("passed").sum()),
        "explanations_failed": int(local["explanation_status"].eq("failed").sum()),
        "maximum_decision_score_difference": float(local["decision_score_difference"].max()),
        "maximum_probability_difference": float(local["probability_difference"].max()),
        "invalid_reason_code_count": int(invalid_reason_count),
        "excluded_feature_violations": sorted(excluded_violations),
        "missing_feature_count": missing_feature_count,
        "overall_status": (
            "passed"
            if local["explanation_status"].eq("passed").all()
            and invalid_reason_count == 0
            and not excluded_violations
            else "failed"
        ),
        "synthetic_data_statement": "All explained transactions and labels are synthetic.",
    }
    return local, contributions, reasons, quality


def build_error_type_analysis(
    local: pd.DataFrame, contributions: pd.DataFrame, reasons: pd.DataFrame
) -> pd.DataFrame:
    """Summarise explanation behaviour for every prediction outcome category."""
    rows = []
    for error_type in ("true_positive", "false_positive", "true_negative", "false_negative"):
        subset = local[local["error_type"].eq(error_type)]
        transaction_ids = set(subset["transaction_id"])
        contribution_subset = contributions[
            contributions["transaction_id"].isin(transaction_ids)
        ]
        reason_subset = reasons[reasons["transaction_id"].isin(transaction_ids)]
        positive = reason_subset[reason_subset["reason_direction"].eq("positive")]
        negative = reason_subset[reason_subset["reason_direction"].eq("negative")]
        source_counts = Counter(reason_subset["source_feature_name"])
        rows.append(
            {
                "error_type": error_type,
                "transaction_count": int(len(subset)),
                "average_fraud_probability": (
                    float(subset["fraud_probability"].mean()) if not subset.empty else None
                ),
                "average_absolute_contribution": (
                    float(contribution_subset["absolute_contribution"].mean())
                    if not contribution_subset.empty
                    else None
                ),
                "most_common_positive_reason": (
                    positive["reason_code"].mode().iloc[0] if not positive.empty else ""
                ),
                "most_common_negative_reason": (
                    negative["reason_code"].mode().iloc[0] if not negative.empty else ""
                ),
                "dominant_source_features": json.dumps(
                    [name for name, _ in source_counts.most_common(3)]
                ),
                "interpretation": (
                    "No transactions in this outcome group."
                    if subset.empty
                    else "Associations describe model behaviour, not causes or confirmed outcomes."
                ),
            }
        )
    return pd.DataFrame(rows)


def select_investigator_samples(local: pd.DataFrame, sample_size: int) -> pd.DataFrame:
    """Select deterministic representative transactions without duplication."""
    candidates: list[str] = []
    if not local.empty:
        candidates.extend(
            [
                local.sort_values(
                    ["fraud_probability", "transaction_id"], ascending=[False, True]
                ).iloc[0]["transaction_id"],
                local.sort_values(
                    ["fraud_probability", "transaction_id"], ascending=[True, True]
                ).iloc[0]["transaction_id"],
            ]
        )
    for error_type in ("true_positive", "false_positive", "true_negative", "false_negative"):
        subset = local[local["error_type"].eq(error_type)].sort_values(
            ["fraud_probability", "transaction_id"], ascending=[False, True]
        )
        if not subset.empty:
            candidates.append(subset.iloc[0]["transaction_id"])
    unique = list(dict.fromkeys(candidates))[:sample_size]
    return local.set_index("transaction_id").loc[unique].reset_index() if unique else local.head(0)


def write_investigator_packets(
    samples: pd.DataFrame, output_dir: Path, model_identifier: str
) -> list[Path]:
    """Write limited transaction explanation packets for investigator review."""
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for row in samples.itertuples():
        path = output_dir / f"{row.transaction_id}.md"
        positive = json.loads(row.positive_reasons_json)
        negative = json.loads(row.negative_reasons_json)
        lines = [
            f"# Transaction Explanation: {row.transaction_id}",
            "",
            f"- Model: `{model_identifier}`",
            f"- Fraud probability: {row.fraud_probability:.6f}",
            f"- Selected threshold: {row.selected_threshold:.6f}",
            f"- Predicted synthetic label: {row.predicted_fraud_label}",
            f"- Actual synthetic label: {row.actual_fraud_label}",
            f"- Error type: `{row.error_type}`",
            f"- Reconstruction status: `{row.explanation_status}`",
            "",
            "## Factors Increasing The Model Score",
            "",
        ]
        lines.extend(
            f"- {item['human_readable_reason']} Contribution: {item['contribution']:.6f}."
            for item in positive
        )
        if not positive:
            lines.append("No positive contribution exceeded the configured minimum.")
        lines.extend(["", "## Factors Decreasing The Model Score", ""])
        lines.extend(
            f"- {item['human_readable_reason']} Contribution: {item['contribution']:.6f}."
            for item in negative
        )
        if not negative:
            lines.append("No negative contribution exceeded the configured minimum.")
        lines.extend(
            [
                "",
                "## Interpretation",
                "",
                "These contributions explain this model score using synthetic inputs. They are "
                "associations, not causal findings or proof of fraud or criminal conduct.",
                "",
                "A human reviewer must consider source evidence, context, data quality, and "
                "plausible legitimate explanations before taking any action.",
                "",
                "All identifiers, features, labels, and outcomes in this packet are synthetic.",
            ]
        )
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        paths.append(path)
    return paths


def build_explainability_summary(
    metadata: dict[str, Any],
    global_importance: pd.DataFrame,
    source_importance: pd.DataFrame,
    local: pd.DataFrame,
    reasons: pd.DataFrame,
    quality: dict[str, Any],
    error_analysis: pd.DataFrame,
    transactions_available: int,
    top_count: int,
) -> dict[str, Any]:
    """Build portfolio-level explanation metrics and limitations."""
    positives = global_importance[global_importance["direction"].eq("positive")].nlargest(
        top_count, "coefficient"
    )
    negatives = global_importance[global_importance["direction"].eq("negative")].nsmallest(
        top_count, "coefficient"
    )
    common_reasons = reasons["reason_code"].value_counts().head(top_count).to_dict()
    return {
        "run_timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
        "model_identifier": metadata.get("model_version", "fraud-baseline"),
        "model_type": metadata.get("model_type", "LogisticRegression"),
        "transactions_available": int(transactions_available),
        "transactions_explained": int(len(local)),
        "transformed_features": int(len(global_importance)),
        "source_features": int(len(source_importance)),
        "highest_global_positive_associations": positives[
            ["transformed_feature_name", "coefficient"]
        ].to_dict(orient="records"),
        "highest_global_negative_associations": negatives[
            ["transformed_feature_name", "coefficient"]
        ].to_dict(orient="records"),
        "common_local_reason_codes": {
            str(key): int(value) for key, value in common_reasons.items()
        },
        "explanation_quality_metrics": quality,
        "error_type_analysis": error_analysis.to_dict(orient="records"),
        "overall_status": quality["overall_status"],
        "known_limitations": [
            "Coefficients and contributions are model associations, not causal explanations.",
            "Synthetic labels contain weak behavioural signal and produce many false positives.",
            "One-hot levels are aggregated for readability but remain separate model terms.",
            "Explanations describe the persisted baseline only and require human interpretation.",
        ],
        "synthetic_data_statement": "All explanation inputs and outputs are synthetic.",
    }


def write_explainability_outputs(
    global_importance: pd.DataFrame,
    source_importance: pd.DataFrame,
    local: pd.DataFrame,
    contributions: pd.DataFrame,
    reasons: pd.DataFrame,
    quality: dict[str, Any],
    error_analysis: pd.DataFrame,
    summary: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Path]:
    """Write all machine-readable explainability outputs."""
    paths = {
        "global": Path(config["coefficient_output_path"]),
        "source_global": Path(config["source_importance_output_path"]),
        "local": Path(config["local_explanation_output_path"]),
        "contributions": Path(config["contribution_output_path"]),
        "reasons": Path(config["reason_code_output_path"]),
        "quality": Path(config["quality_output_path"]),
        "error_types": Path(config["error_type_output_path"]),
        "summary": Path(config["summary_output_path"]),
    }
    for path in paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    global_importance.to_csv(paths["global"], index=False)
    source_importance.to_csv(paths["source_global"], index=False)
    local.to_csv(paths["local"], index=False)
    contributions.to_csv(paths["contributions"], index=False)
    reasons.to_csv(paths["reasons"], index=False)
    error_analysis.to_csv(paths["error_types"], index=False)
    paths["quality"].write_text(json.dumps(quality, indent=2) + "\n", encoding="utf-8")
    paths["summary"].write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return paths


def write_explainability_report(
    summary: dict[str, Any], output_path: Path
) -> None:
    """Write the human-readable model explainability report."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    quality = summary["explanation_quality_metrics"]
    lines = [
        "# Fraud Model Explainability Report",
        "",
        f"- Model: `{summary['model_identifier']}` ({summary['model_type']})",
        f"- Transactions explained: {summary['transactions_explained']}",
        f"- Transformed features: {summary['transformed_features']}",
        f"- Source features: {summary['source_features']}",
        f"- Explanation quality: `{summary['overall_status']}`",
        f"- Passed / failed: {quality['explanations_passed']} / {quality['explanations_failed']}",
        f"- Maximum decision difference: {quality['maximum_decision_score_difference']:.3e}",
        f"- Maximum probability difference: {quality['maximum_probability_difference']:.3e}",
        "",
        "## Methodology",
        "",
        "For each transformed input, local contribution equals transformed value multiplied by "
        "its Logistic Regression coefficient. Contributions plus the intercept reconstruct the "
        "decision score; applying the logistic function reconstructs probability.",
        "",
        "## Strongest Positive Associations",
        "",
    ]
    lines.extend(
        f"- `{row['transformed_feature_name']}`: {row['coefficient']:.6f}"
        for row in summary["highest_global_positive_associations"]
    )
    lines.extend(["", "## Strongest Negative Associations", ""])
    lines.extend(
        f"- `{row['transformed_feature_name']}`: {row['coefficient']:.6f}"
        for row in summary["highest_global_negative_associations"]
    )
    lines.extend(["", "## Common Local Reason Codes", ""])
    lines.extend(
        f"- `{code}`: {count}" for code, count in summary["common_local_reason_codes"].items()
    )
    lines.extend(
        [
            "",
            "## False Positives And Limitations",
            "",
            "The synthetic baseline produces many false positives. Explanations show which model "
            "associations drove those scores; they do not make the predictions correct or causal.",
            "",
            "Coefficients and local contributions describe model behaviour, not real-world causes, "
            "customer intent, fraud, or criminal conduct. Categorical levels remain encoded model "
            "terms even when aggregated to source features for readability.",
            "",
            "Explanations require trained human interpretation, source-data review, model-version "
            "linkage, reproducibility controls, and documented challenge before any action.",
            "",
            "All explanation inputs, labels, identifiers, and outputs are synthetic.",
        ]
    )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
