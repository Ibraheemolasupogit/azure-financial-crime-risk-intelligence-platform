"""Deterministic and explainable AML transaction-monitoring rules."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, deque
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

ALERT_COLUMNS = [
    "alert_id",
    "transaction_id",
    "account_id",
    "customer_id",
    "rule_id",
    "rule_name",
    "alert_timestamp",
    "transaction_timestamp",
    "alert_severity",
    "risk_points",
    "reason",
    "evidence_json",
    "investigation_status",
    "synthetic_data_flag",
]

CUSTOMER_SUMMARY_COLUMNS = [
    "customer_id",
    "total_aml_alerts",
    "distinct_rules_triggered",
    "low_severity_alerts",
    "medium_severity_alerts",
    "high_severity_alerts",
    "critical_severity_alerts",
    "total_aml_risk_points",
    "maximum_alert_severity",
    "high_value_alert_count",
    "structuring_alert_count",
    "geography_alert_count",
    "device_session_alert_count",
    "kyc_watchlist_alert_count",
    "first_alert_timestamp",
    "latest_alert_timestamp",
    "recommended_review_priority",
]

RULE_NAMES = {
    "AML001": "High-value transaction",
    "AML002": "Structuring or smurfing",
    "AML003": "Rapid movement of funds",
    "AML004": "High-risk geography",
    "AML005": "Unusual cross-border activity",
    "AML006": "Dormant or low-activity account reactivation",
    "AML007": "Repeated failed transactions",
    "AML008": "Device or session risk",
    "AML009": "KYC, PEP, sanctions, or watchlist exposure",
    "AML010": "Unusual merchant or channel pattern",
}

REQUIRED_PREPARED_COLUMNS = {
    "transaction_id",
    "account_id",
    "customer_id",
    "transaction_timestamp",
    "amount",
    "transaction_type",
    "channel",
    "merchant_category",
    "merchant_country",
    "is_cross_border",
    "transaction_status",
    "device_id",
    "session_id",
    "ip_country",
    "login_success",
    "authentication_method",
    "session_risk_signal",
    "customer_country",
    "kyc_status",
    "pep_flag",
    "sanctions_screening_status",
    "account_status",
    "new_device_flag",
    "country_mismatch_flag",
    "aml_watchlist_flag",
}

SEVERITY_ORDER = {"low": 1, "medium": 2, "high": 3, "critical": 4}


def load_aml_config(config_path: Path | str = "configs/aml_rules_config.yaml") -> dict[str, Any]:
    """Load and validate the local AML rule configuration."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"AML rule configuration not found: {path}")
    with path.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)
    if not isinstance(config, dict):
        raise ValueError(f"AML rule configuration must be a mapping: {path}")
    enabled = config.get("enabled_rules", [])
    unknown = sorted(set(enabled) - set(RULE_NAMES))
    if unknown:
        raise ValueError(f"Unknown enabled AML rules: {unknown}")
    for key in ("rule_severity", "rule_risk_points"):
        missing = sorted(set(enabled) - set(config.get(key, {})))
        if missing:
            raise ValueError(f"{key} is missing enabled rules: {missing}")
    return config


def _require_columns(dataframe: pd.DataFrame, required: set[str], name: str) -> None:
    missing = sorted(required - set(dataframe.columns))
    if missing:
        raise ValueError(f"{name} is missing required columns: {missing}")


def _as_bool(series: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(series):
        return series.fillna(False)
    return series.astype(str).str.lower().map({"true": True, "false": False}).fillna(False)


def prepare_aml_data(
    datasets: dict[str, pd.DataFrame], transaction_features: pd.DataFrame
) -> pd.DataFrame:
    """Join validated raw entities and selected prior-only feature signals."""
    required_datasets = {
        "customers",
        "accounts",
        "transactions",
        "device_sessions",
        "aml_watchlist",
    }
    missing_datasets = sorted(required_datasets - set(datasets))
    if missing_datasets:
        raise ValueError(f"Missing AML input datasets: {missing_datasets}")

    transactions = datasets["transactions"].copy()
    _require_columns(
        transactions,
        {
            "transaction_id",
            "account_id",
            "customer_id",
            "transaction_timestamp",
            "amount",
            "transaction_type",
            "channel",
            "merchant_category",
            "merchant_country",
            "is_cross_border",
            "transaction_status",
            "device_id",
            "session_id",
        },
        "transactions",
    )
    transactions["transaction_timestamp"] = pd.to_datetime(
        transactions["transaction_timestamp"], errors="coerce"
    )
    invalid_timestamps = int(transactions["transaction_timestamp"].isna().sum())
    if invalid_timestamps:
        raise ValueError(f"transactions contains {invalid_timestamps} invalid timestamps.")
    transactions["amount"] = pd.to_numeric(transactions["amount"], errors="coerce")
    if transactions["amount"].isna().any():
        raise ValueError("transactions.amount contains non-numeric values.")
    transactions["is_cross_border"] = _as_bool(transactions["is_cross_border"])

    sessions = datasets["device_sessions"][
        [
            "session_id",
            "ip_country",
            "login_success",
            "authentication_method",
            "session_risk_signal",
        ]
    ].drop_duplicates("session_id")
    sessions["login_success"] = _as_bool(sessions["login_success"])
    customers = datasets["customers"][
        [
            "customer_id",
            "country",
            "kyc_status",
            "pep_flag",
            "sanctions_screening_status",
        ]
    ].rename(columns={"country": "customer_country"})
    customers["pep_flag"] = _as_bool(customers["pep_flag"])
    accounts = datasets["accounts"][["account_id", "account_status"]]
    watchlist_customers = set(datasets["aml_watchlist"]["customer_id"].astype(str))

    feature_columns = [
        column
        for column in ["transaction_id", "new_device_flag", "country_mismatch_flag"]
        if column in transaction_features.columns
    ]
    if "transaction_id" not in feature_columns:
        raise ValueError("transaction_features is missing required column: transaction_id")
    features = transaction_features[feature_columns].drop_duplicates("transaction_id")

    prepared = transactions.merge(sessions, on="session_id", how="left", validate="many_to_one")
    prepared = prepared.merge(customers, on="customer_id", how="left", validate="many_to_one")
    prepared = prepared.merge(accounts, on="account_id", how="left", validate="many_to_one")
    prepared = prepared.merge(features, on="transaction_id", how="left", validate="one_to_one")
    prepared["new_device_flag"] = prepared.get("new_device_flag", 0).fillna(0).astype(int)
    prepared["country_mismatch_flag"] = (
        prepared.get("country_mismatch_flag", 0).fillna(0).astype(int)
    )
    prepared["aml_watchlist_flag"] = (
        prepared["customer_id"].astype(str).isin(watchlist_customers).astype(int)
    )
    _require_columns(prepared, REQUIRED_PREPARED_COLUMNS, "prepared AML data")
    return prepared.sort_values(
        ["transaction_timestamp", "transaction_id"], kind="stable"
    ).reset_index(drop=True)


def assign_rule_severity(rule_id: str, config: dict[str, Any]) -> str:
    """Return configured rule severity with domain validation."""
    severity = str(config["rule_severity"][rule_id]).lower()
    if severity not in SEVERITY_ORDER:
        raise ValueError(f"Unsupported severity for {rule_id}: {severity}")
    return severity


def calculate_rule_risk_points(rule_id: str, config: dict[str, Any]) -> int:
    """Return configured, traceable integer risk points."""
    points = int(config["rule_risk_points"][rule_id])
    if points < 0:
        raise ValueError(f"Risk points cannot be negative for {rule_id}.")
    return points


def generate_alert_evidence(evidence: dict[str, Any]) -> str:
    """Serialize machine-readable evidence deterministically."""
    clean = {
        key: value.isoformat() if isinstance(value, (pd.Timestamp, datetime)) else value
        for key, value in evidence.items()
    }
    return json.dumps(clean, sort_keys=True, separators=(",", ":"))


def _deterministic_alert_id(rule_id: str, transaction_id: str) -> str:
    digest = hashlib.sha256(f"{rule_id}|{transaction_id}".encode()).hexdigest()[:16]
    return f"AML-{digest.upper()}"


def _empty_alerts() -> pd.DataFrame:
    return pd.DataFrame(columns=ALERT_COLUMNS)


def _create_alert(
    row: pd.Series,
    rule_id: str,
    reason: str,
    evidence: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    return {
        "alert_id": _deterministic_alert_id(rule_id, str(row["transaction_id"])),
        "transaction_id": row["transaction_id"],
        "account_id": row["account_id"],
        "customer_id": row["customer_id"],
        "rule_id": rule_id,
        "rule_name": RULE_NAMES[rule_id],
        "alert_timestamp": pd.Timestamp(config["reference_timestamp"]).isoformat(),
        "transaction_timestamp": pd.Timestamp(row["transaction_timestamp"]).isoformat(),
        "alert_severity": assign_rule_severity(rule_id, config),
        "risk_points": calculate_rule_risk_points(rule_id, config),
        "reason": reason,
        "evidence_json": generate_alert_evidence(evidence),
        "investigation_status": "open",
        "synthetic_data_flag": True,
    }


def _alerts_frame(alerts: list[dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame(alerts, columns=ALERT_COLUMNS) if alerts else _empty_alerts()


def evaluate_aml001(data: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    """AML001: flag transactions over the configured high-value threshold."""
    threshold = float(config["high_value_transaction_threshold"])
    alerts = []
    for _, row in data[data["amount"] > threshold].iterrows():
        evidence = {
            "transaction_amount": float(row["amount"]),
            "configured_threshold": threshold,
            "transaction_type": row["transaction_type"],
            "channel": row["channel"],
            "merchant_country": row["merchant_country"],
        }
        reason = f"Transaction amount {row['amount']:.2f} exceeded {threshold:.2f}."
        alerts.append(_create_alert(row, "AML001", reason, evidence, config))
    return _alerts_frame(alerts)


def evaluate_aml002(data: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    """AML002: detect prior-only rolling structuring patterns."""
    window = timedelta(hours=int(config["structuring_window_hours"]))
    reporting = float(config["structuring_reporting_threshold"])
    aggregate = float(config["structuring_aggregate_threshold"])
    minimum_count = int(config["structuring_minimum_transaction_count"])
    alerts = []
    for _, group in data.groupby("customer_id", sort=False):
        active: deque[tuple[pd.Timestamp, float]] = deque()
        running_amount = 0.0
        for _, row in group.iterrows():
            current_time = row["transaction_timestamp"]
            while active and active[0][0] < current_time - window:
                _, old_amount = active.popleft()
                running_amount -= old_amount
            amount = float(row["amount"])
            if amount < reporting:
                active.append((current_time, amount))
                running_amount += amount
                if len(active) >= minimum_count and running_amount >= aggregate:
                    evidence = {
                        "transaction_count": len(active),
                        "cumulative_amount": round(running_amount, 2),
                        "rolling_window_hours": int(config["structuring_window_hours"]),
                        "reporting_threshold": reporting,
                        "aggregate_threshold": aggregate,
                    }
                    reason = (
                        f"{len(active)} sub-threshold transactions totalled "
                        f"{running_amount:.2f} within "
                        f"{int(config['structuring_window_hours'])} hours."
                    )
                    alerts.append(_create_alert(row, "AML002", reason, evidence, config))
    return _alerts_frame(alerts)


def evaluate_aml003(data: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    """AML003: detect rapid material movement using the immediately prior event."""
    maximum_minutes = float(config["rapid_movement_window_minutes"])
    minimum_amount = float(config["rapid_movement_minimum_amount"])
    alerts = []
    for _, group in data.groupby("customer_id", sort=False):
        previous: pd.Series | None = None
        for _, row in group.iterrows():
            if previous is not None:
                elapsed = (
                    row["transaction_timestamp"] - previous["transaction_timestamp"]
                ).total_seconds() / 60
                channel_change = row["channel"] != previous["channel"]
                country_change = row["merchant_country"] != previous["merchant_country"]
                material = float(row["amount"]) >= minimum_amount
                prior_material = float(previous["amount"]) >= minimum_amount
                if elapsed <= maximum_minutes and material and (
                    prior_material or channel_change or country_change
                ):
                    evidence = {
                        "prior_transaction_timestamp": previous["transaction_timestamp"],
                        "elapsed_minutes": round(elapsed, 2),
                        "current_amount": float(row["amount"]),
                        "prior_amount": float(previous["amount"]),
                        "channel_change": bool(channel_change),
                        "country_change": bool(country_change),
                        "configured_window_minutes": maximum_minutes,
                        "configured_minimum_amount": minimum_amount,
                    }
                    reason = (
                        f"Material activity occurred {elapsed:.2f} minutes after the prior "
                        "transaction."
                    )
                    alerts.append(_create_alert(row, "AML003", reason, evidence, config))
            previous = row
    return _alerts_frame(alerts)


def evaluate_aml004(data: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    """AML004: identify illustrative geography risk or unexpected mismatch."""
    configured = set(config["high_risk_countries"])
    alerts = []
    for _, row in data.iterrows():
        listed = row["merchant_country"] in configured or row["ip_country"] in configured
        mismatch = (
            row["ip_country"] != row["customer_country"]
            and row["merchant_country"] != row["customer_country"]
        )
        if listed or mismatch:
            classification = "illustrative configured list" if listed else "unexpected mismatch"
            evidence = {
                "customer_country": row["customer_country"],
                "merchant_country": row["merchant_country"],
                "ip_country": row["ip_country"],
                "configured_geography_classification": classification,
                "cross_border_indicator": bool(row["is_cross_border"]),
            }
            reason = f"Transaction matched the synthetic geography condition: {classification}."
            alerts.append(_create_alert(row, "AML004", reason, evidence, config))
    return _alerts_frame(alerts)


def evaluate_aml005(data: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    """AML005: detect elevated prior cross-border frequency or ratio."""
    window = timedelta(days=int(config["cross_border_window_days"]))
    count_threshold = int(config["cross_border_count_threshold"])
    ratio_threshold = float(config["cross_border_ratio_threshold"])
    alerts = []
    for _, group in data.groupby("customer_id", sort=False):
        active: deque[tuple[pd.Timestamp, bool, str]] = deque()
        cross_border_count = 0
        countries: Counter[str] = Counter()
        for _, row in group.iterrows():
            current_time = row["transaction_timestamp"]
            while active and active[0][0] < current_time - window:
                _, old_cross_border, old_country = active.popleft()
                cross_border_count -= int(old_cross_border)
                countries[old_country] -= 1
                if countries[old_country] == 0:
                    del countries[old_country]
            prior_count = len(active)
            current_cross_border = bool(row["is_cross_border"])
            current_ratio = (cross_border_count + int(current_cross_border)) / (prior_count + 1)
            trigger = current_cross_border and (
                cross_border_count >= count_threshold
                or (prior_count >= 2 and current_ratio >= ratio_threshold)
            )
            if trigger:
                evidence = {
                    "prior_cross_border_count": cross_border_count,
                    "current_cross_border_ratio": round(current_ratio, 4),
                    "distinct_prior_countries": len(countries),
                    "current_merchant_country": row["merchant_country"],
                    "historical_customer_geography": sorted(countries),
                    "window_days": int(config["cross_border_window_days"]),
                    "count_threshold": count_threshold,
                    "ratio_threshold": ratio_threshold,
                }
                reason = (
                    f"Cross-border activity reached ratio {current_ratio:.2f} with "
                    f"{cross_border_count} prior cross-border events in the window."
                )
                alerts.append(_create_alert(row, "AML005", reason, evidence, config))
            active.append((current_time, current_cross_border, row["merchant_country"]))
            cross_border_count += int(current_cross_border)
            countries[row["merchant_country"]] += 1
    return _alerts_frame(alerts)


def evaluate_aml006(data: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    """AML006: detect material activity after configured account inactivity."""
    dormant_days = int(config["dormant_account_days"])
    material_amount = float(config["dormant_reactivation_amount"])
    alerts = []
    for _, group in data.groupby("account_id", sort=False):
        previous_timestamp: pd.Timestamp | None = None
        for _, row in group.iterrows():
            if previous_timestamp is not None:
                inactivity = (row["transaction_timestamp"] - previous_timestamp).days
                if inactivity >= dormant_days and float(row["amount"]) >= material_amount:
                    evidence = {
                        "inactivity_duration_days": inactivity,
                        "previous_transaction_date": previous_timestamp,
                        "current_transaction_amount": float(row["amount"]),
                        "configured_dormant_days": dormant_days,
                        "configured_material_value_threshold": material_amount,
                        "account_status": row["account_status"],
                    }
                    reason = (
                        f"Material transaction followed {inactivity} days without account activity."
                    )
                    alerts.append(_create_alert(row, "AML006", reason, evidence, config))
            previous_timestamp = row["transaction_timestamp"]
    return _alerts_frame(alerts)


def evaluate_aml007(data: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    """AML007: detect repeated failed transactions in a prior-only rolling window."""
    window = timedelta(hours=int(config["failed_transaction_window_hours"]))
    threshold = int(config["failed_transaction_count_threshold"])
    alerts = []
    for _, group in data.groupby("customer_id", sort=False):
        failures: deque[pd.Timestamp] = deque()
        for _, row in group.iterrows():
            current_time = row["transaction_timestamp"]
            while failures and failures[0] < current_time - window:
                failures.popleft()
            is_failed = row["transaction_status"] != "Approved"
            if is_failed:
                failures.append(current_time)
                if len(failures) >= threshold:
                    evidence = {
                        "failed_transaction_count": len(failures),
                        "rolling_window_hours": int(config["failed_transaction_window_hours"]),
                        "configured_count_threshold": threshold,
                        "account_id": row["account_id"],
                        "channel": row["channel"],
                        "device_id": row["device_id"],
                    }
                    reason = (
                        f"{len(failures)} failed transactions occurred within the configured "
                        "window."
                    )
                    alerts.append(_create_alert(row, "AML007", reason, evidence, config))
    return _alerts_frame(alerts)


def evaluate_aml008(data: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    """AML008: identify risky device, authentication, session, or IP signals."""
    alerts = []
    for _, row in data.iterrows():
        risky_session = row["session_risk_signal"] in {"Medium", "Elevated"}
        failed_login = not bool(row["login_success"])
        unusual_ip = row["ip_country"] != row["customer_country"]
        new_device = bool(row["new_device_flag"])
        if risky_session or failed_login or unusual_ip or new_device:
            evidence = {
                "device_id": row["device_id"],
                "session_id": row["session_id"],
                "authentication_method": row["authentication_method"],
                "login_success": bool(row["login_success"]),
                "ip_country": row["ip_country"],
                "session_risk_signal": row["session_risk_signal"],
                "new_device_indicator": int(row["new_device_flag"]),
                "unusual_ip_geography": bool(unusual_ip),
            }
            conditions = []
            if risky_session:
                conditions.append("session risk")
            if failed_login:
                conditions.append("failed authentication")
            if unusual_ip:
                conditions.append("IP mismatch")
            if new_device:
                conditions.append("new device")
            reason = f"Device or session conditions observed: {', '.join(conditions)}."
            alerts.append(_create_alert(row, "AML008", reason, evidence, config))
    return _alerts_frame(alerts)


def evaluate_aml009(data: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    """AML009: identify synthetic KYC, PEP, screening, or watchlist exposure."""
    alerts = []
    for _, row in data.iterrows():
        kyc_concern = row["kyc_status"] != "Verified"
        pep = bool(row["pep_flag"])
        sanctions_concern = row["sanctions_screening_status"] != "Clear"
        watchlist = bool(row["aml_watchlist_flag"])
        if kyc_concern or pep or sanctions_concern or watchlist:
            evidence = {
                "customer_id": row["customer_id"],
                "kyc_status": row["kyc_status"],
                "pep_flag": pep,
                "sanctions_screening_status": row["sanctions_screening_status"],
                "aml_watchlist_flag": int(watchlist),
            }
            reason = "Synthetic customer due-diligence or watchlist indicators require review."
            alerts.append(_create_alert(row, "AML009", reason, evidence, config))
    return _alerts_frame(alerts)


def evaluate_aml010(data: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    """AML010: identify configured or novel merchant/channel patterns."""
    high_risk_categories = set(config["high_risk_merchant_categories"])
    high_risk_channels = set(config["high_risk_channels"])
    alerts = []
    for _, group in data.groupby("customer_id", sort=False):
        category_counts: Counter[str] = Counter()
        channel_counts: Counter[str] = Counter()
        for _, row in group.iterrows():
            configured_category = row["merchant_category"] in high_risk_categories
            configured_channel = row["channel"] in high_risk_channels
            history_count = sum(category_counts.values())
            novel_pattern = (
                history_count >= 3
                and row["merchant_category"] not in category_counts
                and row["channel"] not in channel_counts
            )
            if configured_category or configured_channel or novel_pattern:
                evidence = {
                    "merchant_category": row["merchant_category"],
                    "channel": row["channel"],
                    "historical_merchant_categories": sorted(category_counts),
                    "historical_channels": sorted(channel_counts),
                    "configured_high_risk_category": bool(configured_category),
                    "configured_high_risk_channel": bool(configured_channel),
                    "novel_pattern": bool(novel_pattern),
                }
                reason = "Merchant or channel activity matched a configured or novel pattern."
                alerts.append(_create_alert(row, "AML010", reason, evidence, config))
            category_counts[row["merchant_category"]] += 1
            channel_counts[row["channel"]] += 1
    return _alerts_frame(alerts)


RULE_EVALUATORS: dict[str, Callable[[pd.DataFrame, dict[str, Any]], pd.DataFrame]] = {
    "AML001": evaluate_aml001,
    "AML002": evaluate_aml002,
    "AML003": evaluate_aml003,
    "AML004": evaluate_aml004,
    "AML005": evaluate_aml005,
    "AML006": evaluate_aml006,
    "AML007": evaluate_aml007,
    "AML008": evaluate_aml008,
    "AML009": evaluate_aml009,
    "AML010": evaluate_aml010,
}


def evaluate_all_enabled_rules(data: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    """Evaluate enabled rule functions and return stable transaction alerts."""
    _require_columns(data, REQUIRED_PREPARED_COLUMNS, "prepared AML data")
    frames = [RULE_EVALUATORS[rule_id](data, config) for rule_id in config["enabled_rules"]]
    non_empty = [frame for frame in frames if not frame.empty]
    if not non_empty:
        return _empty_alerts()
    alerts = pd.concat(non_empty, ignore_index=True)
    return alerts.sort_values(
        ["transaction_timestamp", "rule_id", "transaction_id"], kind="stable"
    ).reset_index(drop=True)


def _review_priority(points: int, config: dict[str, Any]) -> str:
    if points >= int(config["critical_alert_threshold"]):
        return "urgent"
    if points >= int(config["customer_alert_threshold"]):
        return "enhanced"
    if points >= max(1, int(config["customer_alert_threshold"]) // 2):
        return "standard"
    return "routine"


def aggregate_alerts_by_customer(
    alerts: pd.DataFrame, config: dict[str, Any]
) -> pd.DataFrame:
    """Aggregate alert exposure into transparent customer triage features."""
    if alerts.empty:
        return pd.DataFrame(columns=CUSTOMER_SUMMARY_COLUMNS)
    rows = []
    for customer_id, group in alerts.groupby("customer_id", sort=True):
        severity_counts = group["alert_severity"].value_counts()
        maximum = max(group["alert_severity"], key=lambda value: SEVERITY_ORDER[value])
        points = int(group["risk_points"].sum())
        rows.append(
            {
                "customer_id": customer_id,
                "total_aml_alerts": int(len(group)),
                "distinct_rules_triggered": int(group["rule_id"].nunique()),
                "low_severity_alerts": int(severity_counts.get("low", 0)),
                "medium_severity_alerts": int(severity_counts.get("medium", 0)),
                "high_severity_alerts": int(severity_counts.get("high", 0)),
                "critical_severity_alerts": int(severity_counts.get("critical", 0)),
                "total_aml_risk_points": points,
                "maximum_alert_severity": maximum,
                "high_value_alert_count": int(group["rule_id"].eq("AML001").sum()),
                "structuring_alert_count": int(group["rule_id"].eq("AML002").sum()),
                "geography_alert_count": int(group["rule_id"].isin(["AML004", "AML005"]).sum()),
                "device_session_alert_count": int(group["rule_id"].eq("AML008").sum()),
                "kyc_watchlist_alert_count": int(group["rule_id"].eq("AML009").sum()),
                "first_alert_timestamp": group["transaction_timestamp"].min(),
                "latest_alert_timestamp": group["transaction_timestamp"].max(),
                "recommended_review_priority": _review_priority(points, config),
            }
        )
    return pd.DataFrame(rows, columns=CUSTOMER_SUMMARY_COLUMNS)


def _configuration_summary(rule_id: str, config: dict[str, Any]) -> str:
    parameter_map = {
        "AML001": ["high_value_transaction_threshold"],
        "AML002": [
            "structuring_reporting_threshold",
            "structuring_aggregate_threshold",
            "structuring_window_hours",
            "structuring_minimum_transaction_count",
        ],
        "AML003": ["rapid_movement_window_minutes", "rapid_movement_minimum_amount"],
        "AML004": ["high_risk_countries"],
        "AML005": [
            "cross_border_window_days",
            "cross_border_count_threshold",
            "cross_border_ratio_threshold",
        ],
        "AML006": ["dormant_account_days", "dormant_reactivation_amount"],
        "AML007": ["failed_transaction_window_hours", "failed_transaction_count_threshold"],
        "AML008": [],
        "AML009": [],
        "AML010": ["high_risk_channels", "high_risk_merchant_categories"],
    }
    return generate_alert_evidence({key: config[key] for key in parameter_map[rule_id]})


def build_rule_summary(
    alerts: pd.DataFrame, transaction_count: int, config: dict[str, Any]
) -> pd.DataFrame:
    """Summarize configured rule coverage and alert volume."""
    rows = []
    enabled = set(config["enabled_rules"])
    for rule_id, rule_name in RULE_NAMES.items():
        subset = alerts[alerts["rule_id"].eq(rule_id)] if not alerts.empty else alerts
        rows.append(
            {
                "rule_id": rule_id,
                "rule_name": rule_name,
                "enabled": rule_id in enabled,
                "severity": config["rule_severity"].get(rule_id, "not_configured"),
                "risk_points": config["rule_risk_points"].get(rule_id, 0),
                "alert_count": int(len(subset)),
                "affected_customer_count": (
                    int(subset["customer_id"].nunique()) if not subset.empty else 0
                ),
                "percentage_of_transactions": round(
                    (subset["transaction_id"].nunique() / transaction_count * 100)
                    if transaction_count
                    else 0.0,
                    4,
                ),
                "configuration_summary": _configuration_summary(rule_id, config),
            }
        )
    return pd.DataFrame(rows)


def generate_aml_summary_metrics(
    data: pd.DataFrame,
    alerts: pd.DataFrame,
    customer_summary: pd.DataFrame,
    config: dict[str, Any],
) -> dict[str, Any]:
    """Generate machine-readable run metrics without personal details."""
    alerts_by_rule = (
        {
            str(key): int(value)
            for key, value in alerts["rule_id"].value_counts().sort_index().items()
        }
        if not alerts.empty
        else {}
    )
    alerts_by_severity = (
        {
            str(key): int(value)
            for key, value in alerts["alert_severity"].value_counts().sort_index().items()
        }
        if not alerts.empty
        else {}
    )
    top_customers = []
    if not customer_summary.empty:
        top = customer_summary.nlargest(5, ["total_aml_risk_points", "total_aml_alerts"])
        top_customers = top[
            [
                "customer_id",
                "total_aml_alerts",
                "total_aml_risk_points",
                "recommended_review_priority",
            ]
        ].to_dict(orient="records")
    return {
        "run_timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
        "input_row_counts": {"transactions": int(len(data))},
        "enabled_rules": list(config["enabled_rules"]),
        "total_alerts": int(len(alerts)),
        "alerted_transactions": int(alerts["transaction_id"].nunique()) if not alerts.empty else 0,
        "affected_customers": int(alerts["customer_id"].nunique()) if not alerts.empty else 0,
        "alerts_by_rule": alerts_by_rule,
        "alerts_by_severity": alerts_by_severity,
        "highest_risk_customers": top_customers,
        "overall_run_status": "passed",
        "synthetic_data_statement": (
            "All evaluated transactions, entities, indicators, and alerts are synthetic."
        ),
    }


def write_aml_outputs(
    alerts: pd.DataFrame,
    customer_summary: pd.DataFrame,
    rule_summary: pd.DataFrame,
    run_summary: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Path]:
    """Write all AML outputs and return their paths."""
    paths = {
        "alerts": Path(config["alerts_output_path"]),
        "customer_summary": Path(config["customer_summary_output_path"]),
        "rule_summary": Path(config["rule_summary_output_path"]),
        "run_summary": Path(config["run_summary_output_path"]),
    }
    for path in paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    alerts.to_csv(paths["alerts"], index=False)
    customer_summary.to_csv(paths["customer_summary"], index=False)
    rule_summary.to_csv(paths["rule_summary"], index=False)
    paths["run_summary"].write_text(json.dumps(run_summary, indent=2) + "\n", encoding="utf-8")
    return paths


def write_aml_report(
    run_summary: dict[str, Any], rule_summary: pd.DataFrame, output_path: Path
) -> None:
    """Write an investigator-oriented AML rule engine run report."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# AML Rule Engine Report",
        "",
        f"- Run timestamp: `{run_summary['run_timestamp']}`",
        f"- Overall status: `{run_summary['overall_run_status']}`",
        f"- Transactions evaluated: {run_summary['input_row_counts']['transactions']}",
        f"- Enabled rules: {len(run_summary['enabled_rules'])}",
        f"- Total alerts: {run_summary['total_alerts']}",
        f"- Alerted transactions: {run_summary['alerted_transactions']}",
        f"- Affected customers: {run_summary['affected_customers']}",
        "",
        "## Rule Results",
        "",
        "| Rule | Name | Severity | Alerts | Customers | Transaction coverage |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    for row in rule_summary.itertuples():
        lines.append(
            f"| {row.rule_id} | {row.rule_name} | {row.severity} | {row.alert_count} | "
            f"{row.affected_customer_count} | {row.percentage_of_transactions:.2f}% |"
        )
    lines.extend(["", "## Alerts By Severity", ""])
    lines.extend(
        f"- {severity}: {count}"
        for severity, count in run_summary["alerts_by_severity"].items()
    )
    lines.extend(["", "## Highest-Risk Synthetic Customers", ""])
    if run_summary["highest_risk_customers"]:
        lines.extend(
            f"- `{row['customer_id']}`: {row['total_aml_alerts']} alerts, "
            f"{row['total_aml_risk_points']} points, {row['recommended_review_priority']} priority"
            for row in run_summary["highest_risk_customers"]
        )
    else:
        lines.append("No customers generated alerts.")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "Each alert identifies the rule, observed values, configured conditions, severity, "
            "and traceable risk points. Alerts indicate analytical review candidates only; they "
            "do not prove criminal activity or automate a legal or regulatory conclusion.",
            "",
            "The configured country list is synthetic and illustrative. It does not classify any "
            "country or population as inherently criminal.",
        ]
    )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
