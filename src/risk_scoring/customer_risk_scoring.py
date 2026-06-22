"""Transparent customer financial-crime risk scoring for synthetic data."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

COMPONENTS = ["kyc", "transaction_behaviour", "aml_alert", "fraud_model", "device_session"]
COMPONENT_SCORE_COLUMNS = {
    "kyc": "kyc_risk_score",
    "transaction_behaviour": "transaction_behaviour_score",
    "aml_alert": "aml_alert_score",
    "fraud_model": "fraud_model_score",
    "device_session": "device_session_score",
}
RISK_BANDS = {"low", "moderate", "high", "critical"}
REVIEW_PRIORITIES = {"routine", "standard", "enhanced", "urgent"}


def load_risk_config(
    config_path: Path | str = "configs/customer_risk_config.yaml",
) -> dict[str, Any]:
    """Load and validate the customer risk-scoring configuration."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Customer risk configuration not found: {path}")
    with path.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)
    if not isinstance(config, dict):
        raise ValueError(f"Customer risk configuration must be a mapping: {path}")
    validate_risk_config(config)
    return config


def validate_risk_config(config: dict[str, Any]) -> None:
    """Validate weights, caps, mappings, and ordered thresholds."""
    weights = config.get("component_weights", {})
    if set(weights) != set(COMPONENTS):
        raise ValueError(f"component_weights must define exactly: {COMPONENTS}")
    if not np.isclose(sum(float(value) for value in weights.values()), 1.0):
        raise ValueError("Customer risk component weights must sum to 1.0.")
    if any(float(value) < 0 for value in weights.values()):
        raise ValueError("Customer risk component weights cannot be negative.")

    caps = config.get("component_caps", {})
    if set(caps) != set(COMPONENTS) or any(float(value) <= 0 for value in caps.values()):
        raise ValueError("Every component must have a positive score cap.")

    risk = config.get("risk_band_thresholds", {})
    if not (0 <= risk.get("moderate", -1) < risk.get("high", -1) < risk.get("critical", -1) <= 100):
        raise ValueError("Risk-band thresholds must be ordered within 0 to 100.")
    priority = config.get("review_priority_thresholds", {})
    if not (
        0
        <= priority.get("standard", -1)
        < priority.get("enhanced", -1)
        < priority.get("urgent", -1)
        <= 100
    ):
        raise ValueError("Review-priority thresholds must be ordered within 0 to 100.")

    for mapping_name in (
        "kyc_mappings",
        "customer_risk_rating_mappings",
        "sanctions_mappings",
        "aml_severity_points",
    ):
        mapping = config.get(mapping_name)
        if not isinstance(mapping, dict) or not mapping:
            raise ValueError(f"{mapping_name} must be a non-empty mapping.")
        if any(float(value) < 0 for value in mapping.values()):
            raise ValueError(f"{mapping_name} values cannot be negative.")


def _load_csv(path: Path | str, name: str) -> pd.DataFrame:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Required {name} file not found: {file_path}")
    dataframe = pd.read_csv(file_path)
    if dataframe.empty:
        raise ValueError(f"Required {name} file is empty: {file_path}")
    return dataframe


def load_customer_feature_data(path: Path | str) -> pd.DataFrame:
    """Load customer features while removing historical label-derived columns."""
    dataframe = _load_csv(path, "customer features")
    required = {"customer_id", "total_transaction_count", "cross_border_ratio"}
    _require_columns(dataframe, required, "customer features")
    label_columns = [
        column for column in dataframe.columns if column.startswith("historical_fraud_")
    ]
    return dataframe.drop(columns=label_columns)


def load_fraud_prediction_outputs(path: Path | str) -> pd.DataFrame:
    """Load model predictions and retain only scoring-safe columns."""
    dataframe = _load_csv(path, "fraud predictions")
    required = {"transaction_id", "fraud_probability", "predicted_fraud_label"}
    _require_columns(dataframe, required, "fraud predictions")
    return dataframe[["transaction_id", "fraud_probability", "predicted_fraud_label"]].copy()


def load_aml_customer_summaries(path: Path | str) -> pd.DataFrame:
    """Load customer-level AML alert exposure."""
    dataframe = _load_csv(path, "AML customer summary")
    _require_columns(dataframe, {"customer_id", "total_aml_alerts"}, "AML customer summary")
    return dataframe


def _require_columns(dataframe: pd.DataFrame, required: set[str], name: str) -> None:
    missing = sorted(required - set(dataframe.columns))
    if missing:
        raise ValueError(f"{name} is missing required columns: {missing}")


def _as_bool(series: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(series):
        return series.fillna(False)
    return series.astype(str).str.lower().map({"true": True, "false": False}).fillna(False)


def aggregate_fraud_predictions_by_customer(
    fraud_predictions: pd.DataFrame,
    transaction_features: pd.DataFrame,
    config: dict[str, Any],
) -> pd.DataFrame:
    """Aggregate model scores by customer without consulting actual labels or error types."""
    _require_columns(
        fraud_predictions,
        {"transaction_id", "fraud_probability", "predicted_fraud_label"},
        "fraud predictions",
    )
    _require_columns(
        transaction_features, {"transaction_id", "customer_id"}, "transaction features"
    )
    safe_predictions = fraud_predictions[
        ["transaction_id", "fraud_probability", "predicted_fraud_label"]
    ].copy()
    safe_predictions["fraud_probability"] = pd.to_numeric(
        safe_predictions["fraud_probability"], errors="coerce"
    )
    if safe_predictions["fraud_probability"].isna().any():
        raise ValueError("fraud_probability contains non-numeric or missing values.")
    joined = safe_predictions.merge(
        transaction_features[["transaction_id", "customer_id"]],
        on="transaction_id",
        how="left",
        validate="one_to_one",
    )
    if joined["customer_id"].isna().any():
        raise ValueError("Fraud predictions contain transaction IDs without customer mappings.")
    high_threshold = float(config["high_fraud_probability_threshold"])
    joined["high_probability_flag"] = joined["fraud_probability"].ge(high_threshold).astype(int)
    grouped = joined.groupby("customer_id", sort=True).agg(
        fraud_scored_transaction_count=("transaction_id", "count"),
        maximum_fraud_probability=("fraud_probability", "max"),
        average_fraud_probability=("fraud_probability", "mean"),
        predicted_fraud_transaction_count=("predicted_fraud_label", "sum"),
        high_probability_transaction_count=("high_probability_flag", "sum"),
    ).reset_index()
    grouped["predicted_fraud_transaction_ratio"] = grouped[
        "predicted_fraud_transaction_count"
    ] / grouped["fraud_scored_transaction_count"]
    grouped["high_probability_transaction_ratio"] = grouped[
        "high_probability_transaction_count"
    ] / grouped["fraud_scored_transaction_count"]
    return grouped


def prepare_customer_risk_indicators(
    customer_features: pd.DataFrame,
    customer_profiles: pd.DataFrame,
    transaction_features: pd.DataFrame,
    fraud_predictions: pd.DataFrame,
    aml_summary: pd.DataFrame,
    device_sessions: pd.DataFrame,
    config: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Create a minimised customer-level indicator table for scoring."""
    _require_columns(customer_profiles, {"customer_id", "customer_risk_rating"}, "customers")
    _require_columns(
        transaction_features,
        {
            "transaction_id",
            "customer_id",
            "transaction_velocity_score",
            "country_mismatch_flag",
        },
        "transaction features",
    )
    _require_columns(
        device_sessions,
        {"customer_id", "login_success", "session_risk_signal"},
        "device sessions",
    )
    base = customer_features.copy()
    if any(column.startswith("historical_fraud_") for column in base.columns):
        raise ValueError("Historical fraud label columns are prohibited in scoring inputs.")
    base = base.merge(
        customer_profiles[["customer_id", "customer_risk_rating"]],
        on="customer_id",
        how="left",
        validate="one_to_one",
    )

    transaction_aggregates = transaction_features.groupby("customer_id", sort=True).agg(
        maximum_transaction_velocity=("transaction_velocity_score", "max"),
        average_transaction_velocity=("transaction_velocity_score", "mean"),
        geography_mismatch_count=("country_mismatch_flag", "sum"),
    ).reset_index()
    fraud_aggregates = aggregate_fraud_predictions_by_customer(
        fraud_predictions, transaction_features, config
    )
    sessions = device_sessions.copy()
    sessions["login_success"] = _as_bool(sessions["login_success"])
    sessions["failed_authentication"] = (~sessions["login_success"]).astype(int)
    sessions["elevated_session"] = sessions["session_risk_signal"].eq("Elevated").astype(int)
    session_aggregates = sessions.groupby("customer_id", sort=True).agg(
        failed_authentication_count=("failed_authentication", "sum"),
        elevated_session_count=("elevated_session", "sum"),
    ).reset_index()

    for aggregate in (transaction_aggregates, fraud_aggregates, aml_summary, session_aggregates):
        base = base.merge(aggregate, on="customer_id", how="left", validate="one_to_one")
    if "maximum_alert_severity" in base.columns:
        base = base.rename(columns={"maximum_alert_severity": "maximum_aml_severity"})

    numeric_columns = base.select_dtypes(include="number").columns
    missing_before = {column: int(base[column].isna().sum()) for column in numeric_columns}
    missing_statistics = {key: value for key, value in missing_before.items() if value}
    if config["missing_value_handling_policy"] != "zero_for_missing_derived_indicators":
        raise ValueError("Unsupported missing-value handling policy.")
    base[numeric_columns] = base[numeric_columns].fillna(0)
    for column, default in (
        ("maximum_aml_severity", "none"),
        ("customer_risk_rating", "Low"),
    ):
        if column in base.columns:
            base[column] = base[column].fillna(default)
    return base.sort_values("customer_id").reset_index(drop=True), missing_statistics


def normalise_component(raw_value: pd.Series | float, cap: float) -> pd.Series | float:
    """Normalise a non-negative raw measure to the bounded 0-100 scale."""
    if cap <= 0:
        raise ValueError("Component score cap must be positive.")
    if isinstance(raw_value, pd.Series):
        return (raw_value.clip(lower=0, upper=cap) / cap * 100).clip(0, 100)
    return min(max(float(raw_value), 0.0), cap) / cap * 100


def _component_frame(
    data: pd.DataFrame,
    component_name: str,
    raw_points: pd.Series,
    evidence: list[dict[str, Any]],
    reasons: list[str],
    config: dict[str, Any],
) -> pd.DataFrame:
    cap = float(config["component_caps"][component_name])
    score = normalise_component(raw_points, cap).round(4)
    return pd.DataFrame(
        {
            "customer_id": data["customer_id"],
            "component_name": component_name,
            "raw_value_summary": [json.dumps(item, sort_keys=True) for item in evidence],
            "normalised_score": score,
            "configured_weight": float(config["component_weights"][component_name]),
            "weighted_contribution": (
                score * float(config["component_weights"][component_name])
            ).round(4),
            "score_cap": cap,
            "reason": reasons,
            "evidence_json": [json.dumps(item, sort_keys=True) for item in evidence],
        }
    )


def prepare_kyc_risk_indicators(data: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    """Calculate customer-profile and due-diligence risk points."""
    required = {
        "customer_id",
        "kyc_status",
        "pep_flag",
        "sanctions_screening_status",
        "customer_risk_rating",
        "aml_watchlist_flag",
        "customer_tenure_days",
    }
    _require_columns(data, required, "customer risk indicators")
    recency = config["onboarding_recency_thresholds"]
    raw_points = []
    evidence = []
    reasons = []
    for row in data.itertuples():
        tenure = float(row.customer_tenure_days)
        recency_points = 0.0
        if tenure <= float(recency["very_recent_days"]):
            recency_points = float(recency["very_recent_points"])
        elif tenure <= float(recency["recent_days"]):
            recency_points = float(recency["recent_points"])
        values = {
            "kyc_status": row.kyc_status,
            "kyc_points": float(config["kyc_mappings"][row.kyc_status]),
            "customer_risk_rating": row.customer_risk_rating,
            "customer_risk_rating_points": float(
                config["customer_risk_rating_mappings"][row.customer_risk_rating]
            ),
            "pep_flag": bool(row.pep_flag),
            "pep_points": float(config["pep_points"]) if bool(row.pep_flag) else 0.0,
            "sanctions_screening_status": row.sanctions_screening_status,
            "sanctions_points": float(
                config["sanctions_mappings"][row.sanctions_screening_status]
            ),
            "aml_watchlist_flag": int(row.aml_watchlist_flag),
            "watchlist_points": (
                float(config["watchlist_points"]) if bool(row.aml_watchlist_flag) else 0.0
            ),
            "customer_tenure_days": tenure,
            "onboarding_recency_points": recency_points,
        }
        raw_points.append(
            values["kyc_points"]
            + values["customer_risk_rating_points"]
            + values["pep_points"]
            + values["sanctions_points"]
            + values["watchlist_points"]
            + recency_points
        )
        indicators = []
        if row.kyc_status != "Verified":
            indicators.append(f"KYC status is {row.kyc_status}")
        if row.customer_risk_rating != "Low":
            indicators.append(f"synthetic profile rating is {row.customer_risk_rating}")
        if bool(row.pep_flag):
            indicators.append("synthetic PEP indicator is present")
        if row.sanctions_screening_status != "Clear":
            indicators.append(f"screening status is {row.sanctions_screening_status}")
        if bool(row.aml_watchlist_flag):
            indicators.append("synthetic watchlist exposure is present")
        if recency_points:
            indicators.append(f"customer tenure is {int(tenure)} days")
        reasons.append("; ".join(indicators) or "No elevated KYC indicators observed.")
        evidence.append(values)
    return _component_frame(data, "kyc", pd.Series(raw_points), evidence, reasons, config)


def prepare_transaction_behaviour_risk_indicators(
    data: pd.DataFrame, config: dict[str, Any]
) -> pd.DataFrame:
    """Calculate threshold-relative transaction behaviour risk."""
    thresholds = config["transaction_behaviour_thresholds"]
    metrics = [
        ("total_transaction_count", "transaction_count", 15),
        ("total_transaction_amount", "total_transaction_amount", 15),
        ("maximum_transaction_amount", "maximum_transaction_amount", 20),
        ("cross_border_ratio", "cross_border_ratio", 15),
        ("failed_transaction_ratio", "failed_transaction_ratio", 10),
        ("night_transaction_ratio", "night_transaction_ratio", 5),
        ("unique_merchant_country_count", "unique_merchant_country_count", 10),
        ("new_device_transaction_count", "new_device_transaction_count", 5),
        ("maximum_transaction_velocity", "transaction_velocity_score", 5),
    ]
    required = {"customer_id", *(item[0] for item in metrics)}
    _require_columns(data, required, "customer risk indicators")
    raw_points = []
    evidence = []
    reasons = []
    for _, row in data.iterrows():
        values: dict[str, Any] = {}
        points = 0.0
        elevated = []
        for column, threshold_key, maximum_points in metrics:
            value = float(row[column])
            threshold = float(thresholds[threshold_key])
            contribution = min(value / threshold, 1.0) * maximum_points if threshold else 0.0
            values[column] = value
            values[f"{column}_threshold"] = threshold
            values[f"{column}_points"] = round(contribution, 4)
            points += contribution
            if value >= threshold:
                elevated.append(f"{column} reached {value:.2f} against {threshold:.2f}")
        raw_points.append(points)
        evidence.append(values)
        reasons.append(
            "; ".join(elevated[:3])
            or "Transaction behaviour remained below configured thresholds."
        )
    return _component_frame(
        data, "transaction_behaviour", pd.Series(raw_points), evidence, reasons, config
    )


def prepare_aml_alert_risk_indicators(
    data: pd.DataFrame, config: dict[str, Any]
) -> pd.DataFrame:
    """Calculate AML alert exposure from traceable counts and points."""
    columns = [
        "total_aml_alerts",
        "distinct_rules_triggered",
        "low_severity_alerts",
        "medium_severity_alerts",
        "high_severity_alerts",
        "critical_severity_alerts",
        "total_aml_risk_points",
        "high_value_alert_count",
        "structuring_alert_count",
        "geography_alert_count",
        "device_session_alert_count",
        "kyc_watchlist_alert_count",
    ]
    _require_columns(data, {"customer_id", *columns}, "customer risk indicators")
    severity = config["aml_severity_points"]
    raw_points = []
    evidence = []
    reasons = []
    for _, row in data.iterrows():
        values = {column: float(row[column]) for column in columns}
        severity_points = sum(
            float(row[f"{name}_severity_alerts"]) * float(severity[name])
            for name in ("low", "medium", "high", "critical")
        )
        points = (
            float(row["total_aml_risk_points"])
            + severity_points
            + float(row["distinct_rules_triggered"]) * 5
            + float(row["structuring_alert_count"]) * 10
            + float(row["kyc_watchlist_alert_count"]) * 10
        )
        values["configured_severity_points"] = severity
        values["derived_raw_points"] = points
        raw_points.append(points)
        evidence.append(values)
        indicators = []
        if row["high_severity_alerts"] or row["critical_severity_alerts"]:
            indicators.append(
                f"{int(row['high_severity_alerts'] + row['critical_severity_alerts'])} "
                "high/critical AML alerts"
            )
        if row["structuring_alert_count"]:
            indicators.append(f"{int(row['structuring_alert_count'])} structuring alerts")
        if row["total_aml_alerts"]:
            indicators.append(f"{int(row['total_aml_alerts'])} total AML alerts")
        reasons.append("; ".join(indicators) or "No AML alert exposure observed.")
    return _component_frame(data, "aml_alert", pd.Series(raw_points), evidence, reasons, config)


def prepare_fraud_model_risk_indicators(
    data: pd.DataFrame, config: dict[str, Any]
) -> pd.DataFrame:
    """Calculate model-score risk without actual fraud labels."""
    columns = [
        "maximum_fraud_probability",
        "average_fraud_probability",
        "predicted_fraud_transaction_count",
        "high_probability_transaction_count",
        "predicted_fraud_transaction_ratio",
        "high_probability_transaction_ratio",
    ]
    _require_columns(data, {"customer_id", *columns}, "customer risk indicators")
    raw_points = (
        data["maximum_fraud_probability"] * 50
        + data["average_fraud_probability"] * 30
        + data["predicted_fraud_transaction_ratio"] * 10
        + data["high_probability_transaction_ratio"] * 10
    )
    evidence = []
    reasons = []
    for _, row in data.iterrows():
        values = {column: float(row[column]) for column in columns}
        values["fraud_probability_threshold"] = float(config["fraud_probability_threshold"])
        values["high_fraud_probability_threshold"] = float(
            config["high_fraud_probability_threshold"]
        )
        evidence.append(values)
        if row["maximum_fraud_probability"] >= config["high_fraud_probability_threshold"]:
            reasons.append(
                f"Maximum model probability {row['maximum_fraud_probability']:.3f} exceeded "
                f"{config['high_fraud_probability_threshold']:.3f}."
            )
        elif row["predicted_fraud_transaction_count"]:
            reasons.append(
                f"{int(row['predicted_fraud_transaction_count'])} transactions exceeded the "
                "model operating threshold."
            )
        else:
            reasons.append("No elevated fraud-model score observed in available predictions.")
    return _component_frame(data, "fraud_model", raw_points, evidence, reasons, config)


def prepare_device_session_risk_indicators(
    data: pd.DataFrame, config: dict[str, Any]
) -> pd.DataFrame:
    """Calculate device, authentication, session, and geography mismatch risk."""
    thresholds = config["device_risk_thresholds"]
    metrics = [
        ("risky_session_count", 25),
        ("new_device_transaction_count", 20),
        ("failed_authentication_count", 25),
        ("geography_mismatch_count", 20),
        ("elevated_session_count", 10),
    ]
    required = {"customer_id", *(item[0] for item in metrics)}
    _require_columns(data, required, "customer risk indicators")
    raw_points = []
    evidence = []
    reasons = []
    for _, row in data.iterrows():
        values = {"unique_device_count": float(row.get("unique_device_count", 0))}
        points = 0.0
        elevated = []
        for column, maximum_points in metrics:
            value = float(row[column])
            threshold = float(thresholds[column])
            contribution = min(value / threshold, 1.0) * maximum_points if threshold else 0.0
            values[column] = value
            values[f"{column}_threshold"] = threshold
            values[f"{column}_points"] = round(contribution, 4)
            points += contribution
            if value >= threshold:
                elevated.append(f"{column} reached {value:.0f} against {threshold:.0f}")
        raw_points.append(points)
        evidence.append(values)
        reasons.append(
            "; ".join(elevated[:3])
            or "Device and session indicators remained below thresholds."
        )
    return _component_frame(
        data, "device_session", pd.Series(raw_points), evidence, reasons, config
    )


def assign_risk_band(score: float, config: dict[str, Any]) -> str:
    """Assign a configured analytical risk band."""
    thresholds = config["risk_band_thresholds"]
    if score >= float(thresholds["critical"]):
        return "critical"
    if score >= float(thresholds["high"]):
        return "high"
    if score >= float(thresholds["moderate"]):
        return "moderate"
    return "low"


def assign_review_priority(score: float, config: dict[str, Any]) -> str:
    """Assign a configured investigation triage priority."""
    thresholds = config["review_priority_thresholds"]
    if score >= float(thresholds["urgent"]):
        return "urgent"
    if score >= float(thresholds["enhanced"]):
        return "enhanced"
    if score >= float(thresholds["standard"]):
        return "standard"
    return "routine"


def calculate_customer_risk_scores(
    indicators: pd.DataFrame, config: dict[str, Any]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Calculate all components, total scores, reasons, and reconstructable audit rows."""
    validate_risk_config(config)
    prohibited = {
        column
        for column in indicators.columns
        if column in {"fraud_label", "actual_fraud_label"}
        or column.startswith("historical_fraud_")
    }
    if prohibited:
        raise ValueError(
            "Actual or historical fraud labels are prohibited in scoring: "
            f"{sorted(prohibited)}"
        )
    component_frames = [
        prepare_kyc_risk_indicators(indicators, config),
        prepare_transaction_behaviour_risk_indicators(indicators, config),
        prepare_aml_alert_risk_indicators(indicators, config),
        prepare_fraud_model_risk_indicators(indicators, config),
        prepare_device_session_risk_indicators(indicators, config),
    ]
    components = pd.concat(component_frames, ignore_index=True)
    score_wide = components.pivot(
        index="customer_id", columns="component_name", values="normalised_score"
    )
    score_wide = score_wide.rename(columns=COMPONENT_SCORE_COLUMNS).reset_index()
    contributions = components.groupby("customer_id", sort=True)["weighted_contribution"].sum()
    score_wide["total_risk_score"] = score_wide["customer_id"].map(contributions).round(4)
    score_wide["risk_band"] = score_wide["total_risk_score"].map(
        lambda value: assign_risk_band(value, config)
    )
    score_wide["review_priority"] = score_wide["total_risk_score"].map(
        lambda value: assign_review_priority(value, config)
    )

    evidence_lookup = components.set_index(["customer_id", "component_name"])["evidence_json"]
    primary_reasons = []
    secondary_reasons = []
    all_reasons = []
    all_evidence = []
    top_count = int(config["top_reason_count"])
    for customer_id in score_wide["customer_id"]:
        customer_components = components[components["customer_id"].eq(customer_id)].sort_values(
            ["weighted_contribution", "component_name"], ascending=[False, True]
        )
        top = customer_components.head(top_count)
        reasons = [
            {
                "component": row.component_name,
                "reason": row.reason,
                "score": float(row.normalised_score),
                "weighted_contribution": float(row.weighted_contribution),
            }
            for row in top.itertuples()
        ]
        primary_reasons.append(reasons[0]["reason"] if reasons else "No elevated indicators.")
        secondary_reasons.append(reasons[1]["reason"] if len(reasons) > 1 else "")
        all_reasons.append(json.dumps(reasons, sort_keys=True))
        evidence = {
            component: json.loads(evidence_lookup.loc[(customer_id, component)])
            for component in COMPONENTS
        }
        all_evidence.append(json.dumps(evidence, sort_keys=True))
    score_wide["primary_risk_reason"] = primary_reasons
    score_wide["secondary_risk_reason"] = secondary_reasons
    score_wide["top_risk_reasons_json"] = all_reasons
    score_wide["component_evidence_json"] = all_evidence

    passthrough_source = indicators.copy()
    if "sanctions_screening_flag" not in passthrough_source.columns:
        passthrough_source["sanctions_screening_flag"] = (
            passthrough_source["sanctions_screening_status"].ne("Clear").astype(int)
        )
    passthrough = passthrough_source[
        [
            "customer_id",
            "total_aml_alerts",
            "maximum_aml_severity",
            "maximum_fraud_probability",
            "predicted_fraud_transaction_count",
            "risky_session_count",
            "aml_watchlist_flag",
            "pep_flag",
            "sanctions_screening_flag",
        ]
    ].copy()
    output = score_wide.merge(passthrough, on="customer_id", how="left", validate="one_to_one")
    output["scoring_timestamp"] = pd.Timestamp(config["reference_timestamp"]).isoformat()
    output["score_version"] = str(config["score_version"])
    output["synthetic_data_flag"] = True
    return output.sort_values("customer_id").reset_index(drop=True), components.sort_values(
        ["customer_id", "component_name"]
    ).reset_index(drop=True)


def generate_portfolio_risk_summary(
    scores: pd.DataFrame,
    components: pd.DataFrame,
    missing_statistics: dict[str, int],
    config: dict[str, Any],
) -> dict[str, Any]:
    """Generate portfolio-level scoring metrics using identifiers only."""
    average_components = (
        components.groupby("component_name")["normalised_score"].mean().round(4).to_dict()
    )
    dominant = max(average_components, key=average_components.get)
    top = scores.sort_values(
        ["total_risk_score", "customer_id"], ascending=[False, True], kind="stable"
    ).head(5)
    return {
        "run_timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
        "score_version": str(config["score_version"]),
        "customers_scored": int(len(scores)),
        "average_total_risk_score": round(float(scores["total_risk_score"].mean()), 4),
        "median_total_risk_score": round(float(scores["total_risk_score"].median()), 4),
        "minimum_total_risk_score": round(float(scores["total_risk_score"].min()), 4),
        "maximum_total_risk_score": round(float(scores["total_risk_score"].max()), 4),
        "customers_by_risk_band": {
            str(key): int(value) for key, value in scores["risk_band"].value_counts().items()
        },
        "customers_by_review_priority": {
            str(key): int(value)
            for key, value in scores["review_priority"].value_counts().items()
        },
        "average_component_scores": average_components,
        "highest_risk_customers": top[
            ["customer_id", "total_risk_score", "risk_band", "primary_risk_reason"]
        ].to_dict(orient="records"),
        "dominant_risk_component": dominant,
        "missing_data_statistics": missing_statistics,
        "configuration_validation_status": "passed",
        "weights_reconstruct_total": bool(
            np.allclose(
                components.groupby("customer_id")["weighted_contribution"].sum().sort_index(),
                scores.set_index("customer_id")["total_risk_score"].sort_index(),
                atol=0.0001,
            )
        ),
        "overall_run_status": "passed",
        "synthetic_data_statement": "All customer indicators and scores are synthetic.",
    }


def generate_retrospective_evaluation(
    scores: pd.DataFrame,
    fraud_labels: pd.DataFrame,
    transaction_features: pd.DataFrame,
) -> dict[str, Any]:
    """Compare completed scores with labels strictly for retrospective analysis."""
    _require_columns(fraud_labels, {"transaction_id", "fraud_label"}, "fraud labels")
    _require_columns(
        transaction_features, {"transaction_id", "customer_id"}, "transaction features"
    )
    outcomes = fraud_labels[["transaction_id", "fraud_label"]].merge(
        transaction_features[["transaction_id", "customer_id"]],
        on="transaction_id",
        how="left",
        validate="one_to_one",
    )
    customer_outcomes = outcomes.groupby("customer_id")["fraud_label"].max().rename(
        "historical_fraud_customer"
    )
    evaluation = scores[["customer_id", "risk_band"]].merge(
        customer_outcomes, on="customer_id", how="left", validate="one_to_one"
    )
    evaluation["historical_fraud_customer"] = evaluation["historical_fraud_customer"].fillna(0)
    fraud_customers = evaluation[evaluation["historical_fraud_customer"].eq(1)]
    high_or_critical = fraud_customers["risk_band"].isin(["high", "critical"])
    prevalence = evaluation.groupby("risk_band")["historical_fraud_customer"].mean()
    non_fraud_distribution = evaluation[evaluation["historical_fraud_customer"].eq(0)][
        "risk_band"
    ].value_counts()
    return {
        "evaluation_type": "retrospective_only",
        "labels_used_in_scoring": False,
        "customers_with_historical_synthetic_fraud": int(len(fraud_customers)),
        "fraud_prevalence_by_risk_band": {
            str(key): round(float(value), 4) for key, value in prevalence.items()
        },
        "high_or_critical_recall_for_historical_fraud_customers": (
            round(float(high_or_critical.mean()), 4) if len(fraud_customers) else None
        ),
        "non_fraud_customer_risk_band_distribution": {
            str(key): int(value) for key, value in non_fraud_distribution.items()
        },
        "limitation": (
            "Synthetic labels contain weak behavioural signal; this is not robust validation."
        ),
    }


def write_risk_outputs(
    scores: pd.DataFrame,
    components: pd.DataFrame,
    summary: dict[str, Any],
    retrospective: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Path]:
    """Write score, audit, portfolio, and retrospective artifacts."""
    paths = {
        "scores": Path(config["risk_scores_output_path"]),
        "components": Path(config["components_output_path"]),
        "summary": Path(config["summary_output_path"]),
        "retrospective": Path(config["retrospective_output_path"]),
    }
    for path in paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    scores.to_csv(paths["scores"], index=False)
    components.to_csv(paths["components"], index=False)
    paths["summary"].write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    paths["retrospective"].write_text(
        json.dumps(retrospective, indent=2) + "\n", encoding="utf-8"
    )
    return paths


def write_risk_report(
    summary: dict[str, Any], config: dict[str, Any], output_path: Path
) -> None:
    """Write the human-readable customer risk-scoring report."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    weights = config["component_weights"]
    lines = [
        "# Customer Risk Scoring Report",
        "",
        f"- Run timestamp: `{summary['run_timestamp']}`",
        f"- Score version: `{summary['score_version']}`",
        f"- Customers scored: {summary['customers_scored']}",
        f"- Average score: {summary['average_total_risk_score']:.4f}",
        f"- Median score: {summary['median_total_risk_score']:.4f}",
        f"- Score range: {summary['minimum_total_risk_score']:.4f} to "
        f"{summary['maximum_total_risk_score']:.4f}",
        f"- Dominant average component: `{summary['dominant_risk_component']}`",
        f"- Weights reconstruct totals: `{summary['weights_reconstruct_total']}`",
        "",
        "## Methodology",
        "",
        "Each component is capped and normalised to 0-100. The total is the sum of "
        "rounded weighted contributions:",
        "",
        f"`total = {weights['kyc']:.2f} x KYC + "
        f"{weights['transaction_behaviour']:.2f} x transaction + "
        f"{weights['aml_alert']:.2f} x AML + {weights['fraud_model']:.2f} x fraud model + "
        f"{weights['device_session']:.2f} x device/session`",
        "",
        "## Risk Distribution",
        "",
    ]
    lines.extend(
        f"- {band}: {count}" for band, count in summary["customers_by_risk_band"].items()
    )
    lines.extend(["", "## Review Priorities", ""])
    lines.extend(
        f"- {priority}: {count}"
        for priority, count in summary["customers_by_review_priority"].items()
    )
    lines.extend(["", "## Average Component Scores", ""])
    lines.extend(
        f"- {component}: {score:.4f}"
        for component, score in summary["average_component_scores"].items()
    )
    lines.extend(["", "## Highest-Risk Synthetic Identifiers", ""])
    lines.extend(
        f"- `{row['customer_id']}`: {row['total_risk_score']:.4f}, {row['risk_band']}; "
        f"{row['primary_risk_reason']}"
        for row in summary["highest_risk_customers"]
    )
    lines.extend(
        [
            "",
            "## Governance And Limitations",
            "",
            "Risk bands are analytical categories and priorities are investigation triage aids. "
            "Neither independently justifies adverse action or a legal or regulatory decision.",
            "",
            "Actual fraud labels are excluded from scoring and used only in a separately written "
            "retrospective evaluation. Synthetic labels have weak behavioural signal.",
            "",
            "Weights, caps, and thresholds require formal approval, monitoring, fairness review, "
            "data-quality controls, and tuning against investigation capacity before real use.",
        ]
    )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
