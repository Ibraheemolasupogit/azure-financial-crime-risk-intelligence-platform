"""Local deterministic monitoring, drift, and operational control reporting."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

STATUS_ORDER = {"healthy": 0, "warning": 1, "unavailable": 2, "critical": 3}
NUMERIC_FEATURES = [
    "amount",
    "log_transaction_amount",
    "amount_vs_account_average",
    "amount_vs_customer_average",
    "transaction_count_customer_24h",
    "transaction_amount_customer_24h",
    "transaction_velocity_score",
    "cross_border_transaction_count_7d",
    "risky_session_flag",
    "country_mismatch_flag",
]
CATEGORICAL_FEATURES = [
    "channel",
    "transaction_type",
    "merchant_category",
    "merchant_country",
    "transaction_status",
    "session_risk_signal",
]


def _json_safe(value: Any) -> Any:
    """Convert pandas and non-finite values to strict JSON-compatible values."""
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def load_monitoring_config(path: Path | str = "configs/monitoring_config.yaml") -> dict[str, Any]:
    """Load transparent local monitoring settings."""
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Monitoring configuration not found: {config_path}")
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ValueError("Monitoring configuration must be a mapping.")
    return config


def derive_monitoring_periods(
    transactions: pd.DataFrame, timestamp_column: str = "transaction_timestamp"
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, str]]:
    """Deterministically split earlier and later transactions at the temporal midpoint."""
    if timestamp_column not in transactions.columns:
        raise ValueError(f"Missing timestamp column: {timestamp_column}")
    ordered = transactions.copy()
    ordered[timestamp_column] = pd.to_datetime(ordered[timestamp_column], errors="coerce")
    if ordered[timestamp_column].isna().any():
        raise ValueError("Monitoring transactions contain invalid timestamps.")
    ordered = ordered.sort_values([timestamp_column, "transaction_id"], kind="stable")
    split = len(ordered) // 2
    if split == 0 or split == len(ordered):
        raise ValueError("Monitoring requires non-empty baseline and current periods.")
    baseline, current = ordered.iloc[:split].copy(), ordered.iloc[split:].copy()
    periods = {
        "baseline": (
            f"{baseline[timestamp_column].min().isoformat()} to "
            f"{baseline[timestamp_column].max().isoformat()}"
        ),
        "current": (
            f"{current[timestamp_column].min().isoformat()} to "
            f"{current[timestamp_column].max().isoformat()}"
        ),
        "split_timestamp": current[timestamp_column].min().isoformat(),
    }
    return baseline, current, periods


def assign_control_status(value: float, warning: float, critical: float) -> str:
    """Assign a transparent upper-bound control status."""
    if value >= critical:
        return "critical"
    if value >= warning:
        return "warning"
    return "healthy"


def calculate_data_quality_metrics(
    baseline: pd.DataFrame, current: pd.DataFrame, config: dict[str, Any]
) -> pd.DataFrame:
    """Monitor row count, schema, missing values, duplicates, timestamps, and amounts."""
    row_change = abs(len(current) - len(baseline)) / max(len(baseline), 1)
    schema_added = sorted(set(current.columns) - set(baseline.columns))
    schema_removed = sorted(set(baseline.columns) - set(current.columns))
    current_missing = float(current.isna().mean().max()) if len(current.columns) else 0.0
    duplicates = int(current["transaction_id"].duplicated().sum())
    invalid_timestamps = int(
        pd.to_datetime(current["transaction_timestamp"], errors="coerce").isna().sum()
    )
    invalid_amounts = int((pd.to_numeric(current["amount"], errors="coerce").fillna(-1) <= 0).sum())
    rows = [
        (
            "row_count_change",
            row_change,
            config["row_count_change_warning_threshold"],
            assign_control_status(
                row_change,
                config["row_count_change_warning_threshold"],
                config["row_count_change_critical_threshold"],
            ),
        ),
        (
            "schema_change_count",
            len(schema_added) + len(schema_removed),
            0,
            "critical" if schema_added or schema_removed else "healthy",
        ),
        (
            "maximum_missing_value_rate",
            current_missing,
            config["missing_value_warning_threshold"],
            "warning" if current_missing > config["missing_value_warning_threshold"] else "healthy",
        ),
        (
            "duplicate_primary_keys",
            duplicates,
            config["duplicate_key_warning_threshold"],
            "warning" if duplicates > config["duplicate_key_warning_threshold"] else "healthy",
        ),
        (
            "invalid_timestamps",
            invalid_timestamps,
            0,
            "critical" if invalid_timestamps else "healthy",
        ),
        (
            "invalid_monetary_values",
            invalid_amounts,
            0,
            "critical" if invalid_amounts else "healthy",
        ),
    ]
    return pd.DataFrame(
        [
            {
                "dataset": "transaction_features",
                "metric_name": name,
                "baseline_value": len(baseline) if name == "row_count_change" else 0,
                "current_value": value,
                "threshold": threshold,
                "status": status,
                "evidence_json": json.dumps(
                    {"schema_added": schema_added, "schema_removed": schema_removed}
                ),
            }
            for name, value, threshold, status in rows
        ]
    )


def population_stability_index(baseline: pd.Series, current: pd.Series, bins: int = 10) -> float:
    """Calculate finite PSI with quantile bins and safe constant handling."""
    base = pd.to_numeric(baseline, errors="coerce").dropna().to_numpy()
    curr = pd.to_numeric(current, errors="coerce").dropna().to_numpy()
    if len(base) == 0 or len(curr) == 0:
        return 0.0
    if np.all(base == base[0]) and np.all(curr == curr[0]) and base[0] == curr[0]:
        return 0.0
    edges = np.unique(np.quantile(base, np.linspace(0, 1, bins + 1)))
    if len(edges) < 2:
        edges = np.array([-np.inf, base[0], np.inf])
    else:
        edges[0], edges[-1] = -np.inf, np.inf
    base_counts = np.histogram(base, bins=edges)[0] / len(base)
    curr_counts = np.histogram(curr, bins=edges)[0] / len(curr)
    epsilon = 1e-6
    base_counts = np.clip(base_counts, epsilon, None)
    curr_counts = np.clip(curr_counts, epsilon, None)
    return float(np.sum((curr_counts - base_counts) * np.log(curr_counts / base_counts)))


def calculate_numeric_feature_drift(
    baseline: pd.DataFrame, current: pd.DataFrame, config: dict[str, Any]
) -> pd.DataFrame:
    """Calculate descriptive changes and PSI for available numeric features."""
    rows = []
    for feature in NUMERIC_FEATURES:
        if feature not in baseline or feature not in current:
            continue
        base, curr = baseline[feature], current[feature]
        psi = population_stability_index(base, curr)
        base_mean, current_mean = float(base.mean()), float(curr.mean())
        status = assign_control_status(
            psi, config["psi_warning_threshold"], config["psi_critical_threshold"]
        )
        rows.append(
            {
                "feature_name": feature,
                "baseline_mean": base_mean,
                "current_mean": current_mean,
                "baseline_median": float(base.median()),
                "current_median": float(curr.median()),
                "baseline_std": float(base.std(ddof=0)),
                "current_std": float(curr.std(ddof=0)),
                "relative_mean_change": abs(current_mean - base_mean) / max(abs(base_mean), 1e-9),
                "psi": psi,
                "distribution_distance": psi,
                "drift_status": status,
                "status": status,
            }
        )
    return pd.DataFrame(rows).sort_values(["psi", "feature_name"], ascending=[False, True])


def categorical_total_variation(
    baseline: pd.Series, current: pd.Series
) -> tuple[float, int, int, bool]:
    """Calculate category-frequency total variation and category changes."""
    base = baseline.fillna("__MISSING__").astype(str)
    curr = current.fillna("__MISSING__").astype(str)
    categories = sorted(set(base) | set(curr))
    base_freq = base.value_counts(normalize=True).reindex(categories, fill_value=0)
    curr_freq = curr.value_counts(normalize=True).reindex(categories, fill_value=0)
    distance = float(0.5 * np.abs(base_freq - curr_freq).sum())
    return (
        distance,
        len(set(curr) - set(base)),
        int((curr == "__MISSING__").sum()),
        base_freq.idxmax() != curr_freq.idxmax(),
    )


def calculate_categorical_feature_drift(
    baseline: pd.DataFrame, current: pd.DataFrame, config: dict[str, Any]
) -> pd.DataFrame:
    """Calculate categorical total-variation drift and new categories."""
    rows = []
    for feature in CATEGORICAL_FEATURES:
        if feature not in baseline or feature not in current:
            continue
        distance, new_count, missing_count, dominant_change = categorical_total_variation(
            baseline[feature], current[feature]
        )
        status = assign_control_status(
            distance,
            config["distribution_distance_warning_threshold"],
            config["distribution_distance_critical_threshold"],
        )
        rows.append(
            {
                "feature_name": feature,
                "baseline_frequencies_json": json.dumps(
                    baseline[feature].value_counts(normalize=True).round(6).to_dict(),
                    sort_keys=True,
                ),
                "current_frequencies_json": json.dumps(
                    current[feature].value_counts(normalize=True).round(6).to_dict(), sort_keys=True
                ),
                "new_category_count": new_count,
                "missing_category_count": missing_count,
                "total_variation_distance": distance,
                "dominant_category_change": dominant_change,
                "drift_status": status,
                "status": status,
            }
        )
    return pd.DataFrame(rows).sort_values(
        ["total_variation_distance", "feature_name"], ascending=[False, True]
    )


def calculate_fraud_performance(data: pd.DataFrame) -> dict[str, Any]:
    """Calculate safe classification and threshold metrics for a period."""
    if data.empty:
        return {"row_count": 0, "status": "unavailable"}
    actual = data["actual_fraud_label"].astype(int).to_numpy()
    predicted = data["predicted_fraud_label"].astype(int).to_numpy()
    probability = data["fraud_probability"].astype(float).to_numpy()
    tn, fp, fn, tp = confusion_matrix(actual, predicted, labels=[0, 1]).ravel()
    two_classes = len(set(actual)) == 2
    return {
        "row_count": len(data),
        "fraud_probability_mean": float(np.mean(probability)),
        "predicted_positive_rate": float(np.mean(predicted)),
        "actual_fraud_prevalence": float(np.mean(actual)),
        "selected_threshold": float(data["selected_threshold"].iloc[0]),
        "accuracy": float(accuracy_score(actual, predicted)),
        "precision": float(precision_score(actual, predicted, zero_division=0)),
        "recall": float(recall_score(actual, predicted, zero_division=0)),
        "f1": float(f1_score(actual, predicted, zero_division=0)),
        "roc_auc": float(roc_auc_score(actual, probability)) if two_classes else None,
        "average_precision": float(average_precision_score(actual, probability))
        if two_classes
        else None,
        "false_positive_rate": float(fp / (fp + tn)) if fp + tn else 0.0,
        "false_negative_rate": float(fn / (fn + tp)) if fn + tp else 0.0,
        "true_positive": int(tp),
        "false_positive": int(fp),
        "true_negative": int(tn),
        "false_negative": int(fn),
        "status": "available" if two_classes else "limited",
    }


def calculate_fraud_model_monitoring(
    predictions: pd.DataFrame, config: dict[str, Any]
) -> pd.DataFrame:
    """Compare earlier and later held-out prediction performance."""
    ordered = predictions.copy()
    ordered["transaction_timestamp"] = pd.to_datetime(ordered["transaction_timestamp"])
    ordered = ordered.sort_values(["transaction_timestamp", "transaction_id"])
    split = len(ordered) // 2
    baseline = calculate_fraud_performance(ordered.iloc[:split])
    current = calculate_fraud_performance(ordered.iloc[split:])
    rows = []
    for metric in sorted(set(baseline) | set(current)):
        if metric == "status":
            continue
        base_value, current_value = baseline.get(metric), current.get(metric)
        difference = (
            abs(float(current_value) - float(base_value))
            if base_value is not None and current_value is not None
            else None
        )
        status = "healthy"
        if (
            metric == "precision"
            and current_value is not None
            and current_value < config["precision_warning_threshold"]
        ):
            status = "warning"
        elif (
            metric == "recall"
            and current_value is not None
            and current_value < config["recall_warning_threshold"]
        ):
            status = "warning"
        elif (
            metric == "average_precision"
            and current_value is not None
            and current_value < config["average_precision_warning_threshold"]
        ):
            status = "warning"
        elif (
            metric == "false_positive_rate"
            and current_value is not None
            and current_value > config["false_positive_rate_warning_threshold"]
        ):
            status = "warning"
        rows.append(
            {
                "metric_name": metric,
                "baseline_value": base_value,
                "current_value": current_value,
                "absolute_change": difference,
                "status": status,
            }
        )
    return pd.DataFrame(rows)


def calculate_aml_rule_monitoring(
    alerts: pd.DataFrame, transaction_count: int, customer_count: int, config: dict[str, Any]
) -> pd.DataFrame:
    """Monitor AML volume, coverage, concentration, duplication, and zero rules."""
    counts = alerts["rule_id"].value_counts()
    alerted_rate = alerts["transaction_id"].nunique() / max(transaction_count, 1)
    alert_ratio = len(alerts) / max(transaction_count, 1)
    concentration = float(counts.max() / len(alerts)) if len(alerts) else 0.0
    customer_rate = alerts["customer_id"].nunique() / max(customer_count, 1)
    duplicates = int(alerts["alert_id"].duplicated().sum())
    rows = [
        ("total_alerts", len(alerts), None, "healthy"),
        (
            "alerted_transaction_rate",
            alerted_rate,
            config["aml_alert_rate_warning_threshold"],
            assign_control_status(
                alerted_rate,
                config["aml_alert_rate_warning_threshold"],
                config["aml_alert_rate_critical_threshold"],
            ),
        ),
        (
            "alert_to_transaction_ratio",
            alert_ratio,
            config["aml_alert_rate_warning_threshold"],
            "warning" if alert_ratio >= config["aml_alert_rate_warning_threshold"] else "healthy",
        ),
        (
            "affected_customer_rate",
            customer_rate,
            0.9,
            "warning" if customer_rate >= 0.9 else "healthy",
        ),
        (
            "dominant_rule_concentration",
            concentration,
            config["aml_rule_concentration_threshold"],
            "warning" if concentration >= config["aml_rule_concentration_threshold"] else "healthy",
        ),
        ("duplicate_alert_ids", duplicates, 0, "critical" if duplicates else "healthy"),
    ]
    for rule_id in [f"AML{index:03d}" for index in range(1, 11)]:
        rows.append(
            (
                f"rule_volume_{rule_id}",
                int(counts.get(rule_id, 0)),
                0,
                "warning" if counts.get(rule_id, 0) == 0 else "healthy",
            )
        )
    return pd.DataFrame(
        [
            {"metric_name": name, "observed_value": value, "threshold": threshold, "status": status}
            for name, value, threshold, status in rows
        ]
    )


def calculate_customer_risk_monitoring(
    scores: pd.DataFrame, components: pd.DataFrame, summary: dict[str, Any], config: dict[str, Any]
) -> pd.DataFrame:
    """Monitor risk distribution, component dominance, versions, and reconstruction."""
    ordered = scores.sort_values("customer_id")
    split = len(ordered) // 2
    base, current = ordered.iloc[:split], ordered.iloc[split:]
    band_categories = ["low", "moderate", "high", "critical"]
    base_dist = (
        base["risk_band"].value_counts(normalize=True).reindex(band_categories, fill_value=0)
    )
    current_dist = (
        current["risk_band"].value_counts(normalize=True).reindex(band_categories, fill_value=0)
    )
    band_shift = float(0.5 * np.abs(base_dist - current_dist).sum())
    reconstruction = components.groupby("customer_id")["weighted_contribution"].sum().sort_index()
    total = scores.set_index("customer_id")["total_risk_score"].sort_index()
    rows = [
        ("average_total_risk_score", float(scores["total_risk_score"].mean()), None, "healthy"),
        ("median_total_risk_score", float(scores["total_risk_score"].median()), None, "healthy"),
        (
            "high_critical_concentration",
            float(scores["risk_band"].isin(["high", "critical"]).mean()),
            0.5,
            "warning"
            if scores["risk_band"].isin(["high", "critical"]).mean() >= 0.5
            else "healthy",
        ),
        (
            "risk_band_distribution_shift",
            band_shift,
            config["customer_risk_band_shift_threshold"],
            "warning" if band_shift >= config["customer_risk_band_shift_threshold"] else "healthy",
        ),
        (
            "score_reconstruction_max_difference",
            float((reconstruction - total).abs().max()),
            0.0001,
            "critical" if not summary.get("weights_reconstruct_total", False) else "healthy",
        ),
        (
            "score_version_count",
            int(scores["score_version"].nunique()),
            1,
            "critical" if scores["score_version"].nunique() != 1 else "healthy",
        ),
    ]
    return pd.DataFrame(
        [
            {"metric_name": name, "observed_value": value, "threshold": threshold, "status": status}
            for name, value, threshold, status in rows
        ]
    )


def calculate_explainability_monitoring(
    quality: dict[str, Any], config: dict[str, Any]
) -> pd.DataFrame:
    """Treat reconstruction or excluded-feature integrity failures as critical."""
    metrics = {
        "transactions_explained": quality.get("transactions_explained", 0),
        "explanation_failures": quality.get("explanations_failed", 0),
        "maximum_decision_score_difference": quality.get(
            "maximum_decision_score_difference", math.inf
        ),
        "maximum_probability_difference": quality.get("maximum_probability_difference", math.inf),
        "invalid_reason_code_count": quality.get("invalid_reason_code_count", 0),
        "excluded_feature_violation_count": len(quality.get("excluded_feature_violations", [])),
        "missing_feature_count": quality.get("missing_feature_count", 0),
    }
    rows = []
    for name, value in metrics.items():
        critical = (
            (name == "explanation_failures" and value > config["explanation_failure_threshold"])
            or ("difference" in name and value > config["reconstruction_difference_threshold"])
            or (
                name
                in {
                    "invalid_reason_code_count",
                    "excluded_feature_violation_count",
                    "missing_feature_count",
                }
                and value > 0
            )
        )
        rows.append(
            {
                "metric_name": name,
                "observed_value": value,
                "threshold": config["reconstruction_difference_threshold"]
                if "difference" in name
                else 0,
                "status": "critical" if critical else "healthy",
            }
        )
    return pd.DataFrame(rows)


def calculate_genai_monitoring(
    quality: dict[str, Any], prompt_payloads: list[dict[str, Any]], config: dict[str, Any]
) -> pd.DataFrame:
    """Monitor grounding, safety, reproducibility, and disabled network controls."""
    enabled_network = sum(bool(item.get("network_call_enabled")) for item in prompt_payloads)
    metrics = {
        "cases_generated": quality.get("cases_generated", 0),
        "grounding_failures": quality.get("grounding_checks_failed", 0),
        "safety_failures": quality.get("safety_checks_failed", 0),
        "unsupported_numeric_claims": len(quality.get("unsupported_numeric_claims", [])),
        "unsupported_transaction_references": len(
            quality.get("unsupported_transaction_references", [])
        ),
        "unsupported_aml_rule_references": len(quality.get("unsupported_aml_rule_references", [])),
        "prohibited_claim_violations": len(quality.get("prohibited_claim_violations", [])),
        "disclaimer_violations": len(quality.get("disclaimer_violations", [])),
        "word_limit_violations": len(quality.get("word_limit_violations", [])),
        "network_enabled_payloads": enabled_network,
    }
    rows = []
    for name, value in metrics.items():
        critical = name != "cases_generated" and value > 0
        rows.append(
            {
                "metric_name": name,
                "observed_value": value,
                "threshold": 0,
                "status": "critical" if critical else "healthy",
            }
        )
    return pd.DataFrame(rows)


def check_pipeline_and_artefacts(config: dict[str, Any]) -> pd.DataFrame:
    """Check expected stage artifacts for existence, size, parseability, and freshness."""
    reference = pd.Timestamp(config["reference_timestamp"])
    rows = []
    targets = {
        **config["expected_pipeline_stages"],
        **{f"artefact_{i}": path for i, path in enumerate(config["expected_artefacts"], 1)},
    }
    for name, value in targets.items():
        path = Path(value)
        exists = path.exists()
        non_empty = exists and path.stat().st_size > 0
        parseable = non_empty
        if non_empty and path.suffix == ".json":
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                parseable = False
        modified = pd.Timestamp(path.stat().st_mtime, unit="s", tz="UTC") if exists else None
        freshness_hours = (
            max((reference - modified).total_seconds() / 3600, 0) if modified else None
        )
        status = "healthy" if exists and non_empty and parseable else "unavailable"
        if (
            status == "healthy"
            and freshness_hours is not None
            and freshness_hours > config["artefact_freshness_threshold_hours"]
        ):
            status = "warning"
        rows.append(
            {
                "stage_or_artefact": name,
                "path": str(path),
                "exists": exists,
                "non_empty": non_empty,
                "parseable": parseable,
                "freshness_hours": freshness_hours,
                "status": status,
            }
        )
    return pd.DataFrame(rows)


def create_monitoring_alert(
    domain: str,
    control: str,
    metric: str,
    observed: Any,
    baseline: Any,
    threshold: Any,
    status: str,
    reason: str,
    action: str,
    evidence: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    """Create a deterministic traceable monitoring alert."""
    digest = hashlib.sha256(
        f"{domain}|{control}|{metric}|{config['monitoring_version']}".encode()
    ).hexdigest()[:16]
    return {
        "monitoring_alert_id": f"MON-{digest.upper()}",
        "monitoring_domain": domain,
        "control_name": control,
        "metric_name": metric,
        "observed_value": observed,
        "baseline_value": baseline,
        "threshold": threshold,
        "status": status,
        "severity": config["monitoring_severity_mappings"][status],
        "reason": reason,
        "recommended_action": action,
        "evidence_json": json.dumps(
            _json_safe(evidence), sort_keys=True, default=str, allow_nan=False
        ),
        "generated_timestamp": config["reference_timestamp"],
        "monitoring_version": config["monitoring_version"],
        "synthetic_data_flag": True,
    }


def generate_alerts_from_domains(
    domains: dict[str, pd.DataFrame], config: dict[str, Any]
) -> pd.DataFrame:
    """Generate alerts for all non-healthy domain controls."""
    alerts = []
    for domain, frame in domains.items():
        if frame.empty or "status" not in frame:
            continue
        for index, row in frame[~frame["status"].eq("healthy")].iterrows():
            metric = str(
                row.get("metric_name", row.get("feature_name", row.get("stage_or_artefact", index)))
            )
            alerts.append(
                create_monitoring_alert(
                    domain,
                    metric,
                    metric,
                    row.get(
                        "current_value",
                        row.get(
                            "observed_value", row.get("psi", row.get("total_variation_distance"))
                        ),
                    ),
                    row.get("baseline_value"),
                    row.get("threshold"),
                    row["status"],
                    f"Monitoring control {metric} is {row['status']}.",
                    "Human review required; investigate evidence and approve any configuration "
                    "change.",
                    row.to_dict(),
                    config,
                )
            )
    return pd.DataFrame(alerts)


def aggregate_platform_status(domains: dict[str, pd.DataFrame]) -> str:
    """Aggregate mandatory control status transparently."""
    statuses = [
        status for frame in domains.values() if "status" in frame for status in frame["status"]
    ]
    if "critical" in statuses:
        return "critical"
    if "unavailable" in statuses:
        return "unavailable"
    if "warning" in statuses:
        return "warning"
    return "healthy"


def write_monitoring_outputs(
    domains: dict[str, pd.DataFrame],
    alerts: pd.DataFrame,
    summary: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Path]:
    """Write all monitoring metric, alert, summary, and report artifacts."""
    key_paths = {
        "data_quality": "data_quality_output_path",
        "numeric_drift": "numeric_drift_output_path",
        "categorical_drift": "categorical_drift_output_path",
        "fraud_model": "fraud_monitoring_output_path",
        "aml": "aml_monitoring_output_path",
        "customer_risk": "risk_monitoring_output_path",
        "explainability": "explainability_monitoring_output_path",
        "genai": "genai_monitoring_output_path",
        "pipeline": "pipeline_health_output_path",
    }
    paths = {}
    for key, config_key in key_paths.items():
        path = Path(config[config_key])
        path.parent.mkdir(parents=True, exist_ok=True)
        domains[key].to_csv(path, index=False)
        paths[key] = path
    alert_path = Path(config["alerts_output_path"])
    alerts.to_csv(alert_path, index=False)
    paths["alerts"] = alert_path
    summary_path = Path(config["summary_output_path"])
    summary_path.write_text(
        json.dumps(_json_safe(summary), indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    paths["summary"] = summary_path
    report_path = Path(config["report_output_path"])
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Platform Monitoring Report",
        "",
        f"- Overall platform status: `{summary['overall_platform_status']}`",
        f"- Baseline period: {summary['baseline_period']}",
        f"- Current period: {summary['current_period']}",
        f"- Controls: healthy={summary['healthy_control_count']}, "
        f"warning={summary['warning_count']}, critical={summary['critical_count']}, "
        f"unavailable={summary['unavailable_count']}",
        "",
        "## Domain Status",
        "",
    ]
    lines.extend(f"- {name}: `{status}`" for name, status in summary["domain_statuses"].items())
    lines.extend(
        [
            "",
            "## Remediation",
            "",
        "Monitoring recommends human investigation only. Retraining, thresholds, AML rules, "
        "score weights, and risk bands must remain controlled and approved changes.",
            "",
            "All monitoring data and findings are synthetic portfolio artifacts.",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    paths["report"] = report_path
    return paths
