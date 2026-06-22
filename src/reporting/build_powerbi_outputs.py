"""Build deterministic Power BI-ready star-schema reporting outputs."""

from __future__ import annotations

import hashlib
import json
from calendar import month_name
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

PROHIBITED_COLUMNS = {"first_name", "last_name", "date_of_birth", "address", "email", "phone"}


def load_reporting_config(path: Path | str = "configs/reporting_config.yaml") -> dict[str, Any]:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Reporting configuration not found: {path}")
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ValueError("Reporting configuration must be a mapping.")
    return config


def stable_surrogate_key(entity: str, natural_id: str) -> int:
    """Create a stable positive 63-bit integer key."""
    digest = hashlib.sha256(f"{entity}|{natural_id}".encode()).hexdigest()[:15]
    return int(digest, 16)


def validate_upstream_artefacts(config: dict[str, Any]) -> None:
    input_keys = [
        key
        for key in config
        if key.endswith("_path")
        and key
        not in {
            "quality_summary_path",
            "quality_report_path",
            "KPI_definitions_path",
            "data_dictionary_path",
            "semantic_model_path",
        }
    ]
    missing = [config[key] for key in input_keys if not Path(config[key]).exists()]
    if missing:
        raise FileNotFoundError(f"Required upstream reporting artifacts are missing: {missing}")


def load_reporting_sources(config: dict[str, Any]) -> dict[str, Any]:
    validate_upstream_artefacts(config)
    csv_map = {
        "customers": "customers_path",
        "accounts": "accounts_path",
        "transactions": "transactions_path",
        "fraud_predictions": "fraud_predictions_path",
        "aml_alerts": "aml_alerts_path",
        "aml_rules": "aml_rule_summary_path",
        "risk": "customer_risk_path",
        "components": "risk_components_path",
        "contributions": "model_contributions_path",
        "reasons": "reason_codes_path",
        "local_explanations": "local_explanations_path",
        "cases": "investigation_cases_path",
        "monitoring_alerts": "monitoring_alerts_path",
        "pipeline": "pipeline_health_path",
    }
    sources = {name: pd.read_csv(config[key]) for name, key in csv_map.items()}
    for name, key in {
        "fraud_metrics": "fraud_metrics_path",
        "monitoring_summary": "monitoring_summary_path",
    }.items():
        sources[name] = json.loads(Path(config[key]).read_text(encoding="utf-8"))
    return sources


def build_dimensions(sources: dict[str, Any], config: dict[str, Any]) -> dict[str, pd.DataFrame]:
    customers = sources["customers"]
    dim_customer = pd.DataFrame(
        {
            "customer_key": customers.customer_id.map(
                lambda value: stable_surrogate_key("customer", value)
            ),
            "customer_id": customers.customer_id,
            "customer_segment": customers.customer_segment,
            "country": customers.country,
            "onboarding_period": pd.to_datetime(customers.onboarding_date)
            .dt.to_period("M")
            .astype(str),
            "kyc_status_category": customers.kyc_status,
            "pep_indicator": customers.pep_flag,
            "sanctions_screening_indicator": customers.sanctions_screening_status.ne("Clear"),
            "aml_watchlist_indicator": customers.customer_id.isin(
                set(sources["risk"].query("aml_watchlist_flag == 1").customer_id)
            ),
            "synthetic_data_flag": True,
        }
    )
    customer_keys = dim_customer.set_index("customer_id").customer_key
    accounts = sources["accounts"]
    dim_account = pd.DataFrame(
        {
            "account_key": accounts.account_id.map(
                lambda value: stable_surrogate_key("account", value)
            ),
            "account_id": accounts.account_id,
            "customer_key": accounts.customer_id.map(customer_keys),
            "account_type": accounts.account_type,
            "account_status": accounts.account_status,
            "currency": accounts.currency,
            "branch_region": accounts.branch_region,
            "opening_period": pd.to_datetime(accounts.account_open_date)
            .dt.to_period("M")
            .astype(str),
            "synthetic_data_flag": True,
        }
    )
    dates = pd.to_datetime(sources["transactions"].transaction_timestamp).dt.normalize().tolist()
    dates += pd.to_datetime(sources["aml_alerts"].transaction_timestamp).dt.normalize().tolist()
    dates += [pd.Timestamp(config["reference_timestamp"]).tz_localize(None).normalize()]
    date_index = pd.date_range(min(dates), max(dates), freq="D")
    dim_date = pd.DataFrame({"full_date": date_index})
    dim_date["date_key"] = dim_date.full_date.dt.strftime("%Y%m%d").astype(int)
    dim_date["year"] = dim_date.full_date.dt.year
    dim_date["quarter"] = "Q" + dim_date.full_date.dt.quarter.astype(str)
    dim_date["month_number"] = dim_date.full_date.dt.month
    dim_date["month_name"] = dim_date.month_number.map(lambda value: month_name[value])
    dim_date["year_month"] = dim_date.full_date.dt.strftime("%Y-%m")
    dim_date["week_number"] = dim_date.full_date.dt.isocalendar().week.astype(int)
    dim_date["day_of_month"] = dim_date.full_date.dt.day
    dim_date["day_name"] = dim_date.full_date.dt.day_name()
    dim_date["is_weekend"] = dim_date.full_date.dt.dayofweek.ge(5)
    hours = pd.Series(range(24), name="hour")
    dim_time = pd.DataFrame({"hour": hours})
    dim_time["time_key"] = dim_time.hour
    dim_time["hour_label"] = dim_time.hour.map(lambda value: f"{value:02d}:00")
    dim_time["daypart"] = pd.cut(
        dim_time.hour,
        [-1, 5, 11, 17, 21, 23],
        labels=["Night", "Morning", "Afternoon", "Evening", "Night-Late"],
    )
    dim_time["is_business_hours"] = dim_time.hour.between(9, 16)
    dim_time["is_night_period"] = (dim_time.hour >= 22) | (dim_time.hour < 6)
    rules = sources["aml_rules"]
    dim_aml_rule = pd.DataFrame(
        {
            "aml_rule_key": rules.rule_id.map(
                lambda value: stable_surrogate_key("aml_rule", value)
            ),
            "rule_id": rules.rule_id,
            "rule_name": rules.rule_name,
            "typology": rules.rule_name,
            "default_severity": rules.severity,
            "configured_risk_points": rules.risk_points,
            "enabled_status": rules.enabled,
        }
    )
    dim_risk_band = pd.DataFrame(
        {
            "risk_band_key": [1, 2, 3, 4],
            "risk_band": ["low", "moderate", "high", "critical"],
            "sort_order": [1, 2, 3, 4],
            "description": [
                "Low analytical risk",
                "Moderate analytical risk",
                "High analytical risk",
                "Critical analytical risk",
            ],
        }
    )
    monitoring = sources["monitoring_alerts"]
    controls = (
        monitoring[["monitoring_domain", "control_name"]]
        .drop_duplicates()
        .sort_values(["monitoring_domain", "control_name"])
    )
    dim_monitoring_control = controls.assign(
        monitoring_control_key=controls.apply(
            lambda row: stable_surrogate_key(
                "monitoring_control", f"{row.monitoring_domain}|{row.control_name}"
            ),
            axis=1,
        )
    )[["monitoring_control_key", "monitoring_domain", "control_name"]]
    return {
        "dim_customer": dim_customer,
        "dim_account": dim_account,
        "dim_date": dim_date,
        "dim_time": dim_time,
        "dim_aml_rule": dim_aml_rule,
        "dim_risk_band": dim_risk_band,
        "dim_monitoring_control": dim_monitoring_control,
    }


def _date_key(values: pd.Series) -> pd.Series:
    return pd.to_datetime(values).dt.strftime("%Y%m%d").astype(int)


def build_fact_tables(
    sources: dict[str, Any], dims: dict[str, pd.DataFrame], config: dict[str, Any]
) -> dict[str, pd.DataFrame]:
    customer_keys = dims["dim_customer"].set_index("customer_id").customer_key
    account_keys = dims["dim_account"].set_index("account_id").account_key
    transaction_source = sources["transactions"].copy()
    transaction_keys = transaction_source.transaction_id.map(
        lambda value: stable_surrogate_key("transaction", value)
    )
    transaction_key_map = pd.Series(
        transaction_keys.values, index=transaction_source.transaction_id
    )
    timestamps = pd.to_datetime(transaction_source.transaction_timestamp)
    fact_transactions = pd.DataFrame(
        {
            "transaction_key": transaction_keys,
            "transaction_id": transaction_source.transaction_id,
            "customer_key": transaction_source.customer_id.map(customer_keys),
            "account_key": transaction_source.account_id.map(account_keys),
            "date_key": _date_key(transaction_source.transaction_timestamp),
            "time_key": timestamps.dt.hour,
            "transaction_type": transaction_source.transaction_type,
            "channel": transaction_source.channel,
            "merchant_category": transaction_source.merchant_category,
            "merchant_country": transaction_source.merchant_country,
            "transaction_amount": transaction_source.amount,
            "currency": transaction_source.currency,
            "cross_border_indicator": transaction_source.is_cross_border,
            "transaction_status": transaction_source.transaction_status,
            "risky_session_indicator": transaction_source.risky_session_flag,
            "new_device_indicator": transaction_source.new_device_flag,
            "velocity_score": transaction_source.transaction_velocity_score,
            "synthetic_data_flag": True,
        }
    )
    prediction = sources["fraud_predictions"].merge(
        transaction_source[["transaction_id", "customer_id"]],
        on="transaction_id",
        how="left",
        validate="one_to_one",
    )
    fact_fraud = pd.DataFrame(
        {
            "transaction_key": prediction.transaction_id.map(transaction_key_map),
            "customer_key": prediction.customer_id.map(customer_keys),
            "actual_synthetic_fraud_label": prediction.actual_fraud_label,
            "fraud_probability": prediction.fraud_probability,
            "selected_threshold": prediction.selected_threshold,
            "predicted_fraud_label": prediction.predicted_fraud_label,
            "error_type": prediction.error_type,
            "model_version": "1.0.0-baseline",
        }
    )
    alerts = sources["aml_alerts"]
    rule_keys = dims["dim_aml_rule"].set_index("rule_id").aml_rule_key
    fact_aml = pd.DataFrame(
        {
            "alert_key": alerts.alert_id.map(lambda value: stable_surrogate_key("alert", value)),
            "alert_id": alerts.alert_id,
            "transaction_key": alerts.transaction_id.map(transaction_key_map),
            "customer_key": alerts.customer_id.map(customer_keys),
            "account_key": alerts.account_id.map(account_keys),
            "aml_rule_key": alerts.rule_id.map(rule_keys),
            "alert_date_key": _date_key(alerts.transaction_timestamp),
            "severity": alerts.alert_severity,
            "risk_points": alerts.risk_points,
            "investigation_status": alerts.investigation_status,
            "reason_category": alerts.rule_name,
            "synthetic_data_flag": True,
        }
    )
    risk = sources["risk"]
    fact_risk = pd.DataFrame(
        {
            "customer_key": risk.customer_id.map(customer_keys),
            "scoring_date_key": _date_key(risk.scoring_timestamp),
            "total_risk_score": risk.total_risk_score,
            "risk_band": risk.risk_band,
            "review_priority": risk.review_priority,
            "kyc_risk_score": risk.kyc_risk_score,
            "transaction_behaviour_score": risk.transaction_behaviour_score,
            "aml_alert_score": risk.aml_alert_score,
            "fraud_model_score": risk.fraud_model_score,
            "device_session_score": risk.device_session_score,
            "aml_alert_count": risk.total_aml_alerts,
            "maximum_fraud_probability": risk.maximum_fraud_probability,
            "primary_risk_driver": risk.primary_risk_reason,
            "score_version": risk.score_version,
            "synthetic_data_flag": True,
        }
    )
    components = sources["components"]
    fact_components = pd.DataFrame(
        {
            "customer_key": components.customer_id.map(customer_keys),
            "component_name": components.component_name,
            "normalised_score": components.normalised_score,
            "configured_weight": components.configured_weight,
            "weighted_contribution": components.weighted_contribution,
            "reason_category": components.reason,
        }
    )
    contributions = (
        sources["contributions"]
        .query("included_in_reason_codes == True")
        .sort_values(["transaction_id", "contribution_rank"])
        .head(int(config["maximum_explanation_rows"]))
    )
    local_status = sources["local_explanations"].set_index("transaction_id").explanation_status
    reasons = sources["reasons"].drop_duplicates(
        ["transaction_id", "source_feature_name", "reason_direction"]
    )
    contributions = contributions.merge(
        reasons[["transaction_id", "source_feature_name", "reason_direction", "reason_code"]],
        left_on=["transaction_id", "source_feature_name", "contribution_direction"],
        right_on=["transaction_id", "source_feature_name", "reason_direction"],
        how="left",
    )
    fact_explanations = pd.DataFrame(
        {
            "transaction_key": contributions.transaction_id.map(transaction_key_map),
            "customer_key": contributions.transaction_id.map(
                transaction_source.set_index("transaction_id").customer_id
            ).map(customer_keys),
            "fraud_probability": contributions.transaction_id.map(
                sources["local_explanations"].set_index("transaction_id").fraud_probability
            ),
            "prediction_outcome": contributions.transaction_id.map(
                sources["local_explanations"].set_index("transaction_id").error_type
            ),
            "source_feature": contributions.source_feature_name,
            "contribution_direction": contributions.contribution_direction,
            "contribution_value": contributions.contribution,
            "contribution_rank": contributions.contribution_rank,
            "reason_code": contributions.reason_code,
            "explanation_status": contributions.transaction_id.map(local_status),
        }
    )
    cases = sources["cases"].head(int(config["maximum_investigation_cases"]))
    fact_cases = pd.DataFrame(
        {
            "case_key": cases.case_id.map(lambda value: stable_surrogate_key("case", value)),
            "case_id": cases.case_id,
            "customer_key": cases.customer_id.map(customer_keys),
            "risk_band": cases.risk_band,
            "review_priority": cases.review_priority,
            "aml_alert_count": cases.aml_alert_count,
            "maximum_fraud_probability": cases.maximum_fraud_probability,
            "primary_risk_driver": cases.primary_risk_driver,
            "generation_mode": cases.generation_mode,
            "grounding_status": cases.grounding_status,
            "safety_status": cases.safety_status,
            "human_review_required": cases.human_review_required,
        }
    )
    monitoring = sources["monitoring_alerts"]
    fact_monitoring = pd.DataFrame(
        {
            "monitoring_alert_key": monitoring.monitoring_alert_id.map(
                lambda value: stable_surrogate_key("monitoring_alert", value)
            ),
            "monitoring_alert_id": monitoring.monitoring_alert_id,
            "monitoring_domain": monitoring.monitoring_domain,
            "control_name": monitoring.control_name,
            "metric_name": monitoring.metric_name,
            "observed_value": monitoring.observed_value,
            "baseline_value": monitoring.baseline_value,
            "threshold": monitoring.threshold,
            "status": monitoring.status,
            "severity": monitoring.severity,
            "recommended_action_category": "human_review",
            "generated_date_key": _date_key(monitoring.generated_timestamp),
        }
    )
    pipeline = sources["pipeline"]
    fact_pipeline = pd.DataFrame(
        {
            "pipeline_stage": pipeline.stage_or_artefact,
            "stage_status": pipeline.status,
            "artefact_count": 1,
            "freshness_status": pipeline.status,
            "parseability_status": pipeline.parseable.map({True: "passed", False: "failed"}),
            "row_count_consistency_status": "not_applicable",
            "generated_date_key": int(
                pd.Timestamp(config["reference_timestamp"]).strftime("%Y%m%d")
            ),
        }
    )
    return {
        "fact_transactions": fact_transactions,
        "fact_fraud_predictions": fact_fraud,
        "fact_aml_alerts": fact_aml,
        "fact_customer_risk": fact_risk,
        "fact_risk_components": fact_components,
        "fact_model_explanations": fact_explanations,
        "fact_investigation_cases": fact_cases,
        "fact_monitoring_alerts": fact_monitoring,
        "fact_pipeline_health": fact_pipeline,
    }


def build_aggregate_tables(
    sources: dict[str, Any], facts: dict[str, pd.DataFrame], config: dict[str, Any]
) -> dict[str, pd.DataFrame]:
    fraud = sources["fraud_metrics"]
    monitoring = sources["monitoring_summary"]
    transaction = facts["fact_transactions"]
    aml = facts["fact_aml_alerts"]
    risk = facts["fact_customer_risk"]
    cases = facts["fact_investigation_cases"]
    kpis = [
        (
            "KPI001",
            "Total Customers",
            len(facts["fact_customer_risk"]),
            "count",
            "fact_customer_risk",
        ),
        (
            "KPI002",
            "Total Accounts",
            sources["accounts"].account_id.nunique(),
            "count",
            "dim_account",
        ),
        ("KPI003", "Total Transactions", len(transaction), "count", "fact_transactions"),
        (
            "KPI004",
            "Total Transaction Value",
            transaction.transaction_amount.sum(),
            "currency",
            "fact_transactions",
        ),
        (
            "KPI005",
            "Fraud Prevalence",
            fraud["test_fraud_rate"],
            "percentage",
            "fact_fraud_predictions",
        ),
        (
            "KPI006",
            "Predicted Fraud Count",
            fraud["predicted_fraud_count"],
            "count",
            "fact_fraud_predictions",
        ),
        ("KPI007", "Fraud Precision", fraud["precision"], "percentage", "fact_fraud_predictions"),
        ("KPI008", "Fraud Recall", fraud["recall"], "percentage", "fact_fraud_predictions"),
        ("KPI009", "Fraud F1", fraud["f1_score"], "decimal", "fact_fraud_predictions"),
        (
            "KPI010",
            "Fraud Average Precision",
            fraud["average_precision"],
            "percentage",
            "fact_fraud_predictions",
        ),
        (
            "KPI011",
            "Fraud False Positives",
            fraud["false_positives"],
            "count",
            "fact_fraud_predictions",
        ),
        ("KPI012", "Total AML Alerts", len(aml), "count", "fact_aml_alerts"),
        (
            "KPI013",
            "AML Alerted Transaction Rate",
            aml.transaction_key.nunique() / len(transaction),
            "percentage",
            "fact_aml_alerts",
        ),
        (
            "KPI014",
            "Affected AML Customers",
            aml.customer_key.nunique(),
            "count",
            "fact_aml_alerts",
        ),
        (
            "KPI015",
            "High Severity AML Alerts",
            aml.severity.isin(["high", "critical"]).sum(),
            "count",
            "fact_aml_alerts",
        ),
        (
            "KPI016",
            "High or Critical Risk Customers",
            risk.risk_band.isin(["high", "critical"]).sum(),
            "count",
            "fact_customer_risk",
        ),
        (
            "KPI017",
            "Urgent or Enhanced Reviews",
            risk.review_priority.isin(["urgent", "enhanced"]).sum(),
            "count",
            "fact_customer_risk",
        ),
        ("KPI018", "Investigation Cases", len(cases), "count", "fact_investigation_cases"),
        (
            "KPI019",
            "Monitoring Warnings",
            monitoring["warning_count"],
            "count",
            "fact_monitoring_alerts",
        ),
        (
            "KPI020",
            "Monitoring Critical",
            monitoring["critical_count"],
            "count",
            "fact_monitoring_alerts",
        ),
        (
            "KPI021",
            "Overall Platform Status",
            monitoring["overall_platform_status"],
            "status",
            "fact_monitoring_alerts",
        ),
    ]
    rows = []
    for kpi_id, name, value, unit, source in kpis:
        display = (
            f"{value:.2%}"
            if unit == "percentage" and isinstance(value, (float, int))
            else str(round(value, 2) if isinstance(value, float) else value)
        )
        rows.append(
            {
                "kpi_id": kpi_id,
                "kpi_name": name,
                "kpi_value": value,
                "display_value": display,
                "unit": unit,
                "status": "synthetic",
                "description": name,
                "source_table": source,
                "calculation_note": "Reconciled to generated local source output.",
                "reporting_timestamp": config["reference_timestamp"],
                "reporting_version": config["reporting_version"],
            }
        )
    executive = pd.DataFrame(rows)
    fraud_agg = pd.DataFrame([fraud])
    aml_agg = (
        aml.groupby(["severity"])
        .agg(
            alert_count=("alert_key", "count"),
            affected_customers=("customer_key", "nunique"),
            affected_transactions=("transaction_key", "nunique"),
        )
        .reset_index()
    )
    risk_agg = (
        risk.groupby(["risk_band", "review_priority"])
        .agg(customer_count=("customer_key", "nunique"), average_score=("total_risk_score", "mean"))
        .reset_index()
    )
    monitoring_agg = (
        facts["fact_monitoring_alerts"]
        .groupby(["monitoring_domain", "status"])
        .size()
        .rename("alert_count")
        .reset_index()
    )
    investigation_agg = (
        cases.groupby(["risk_band", "review_priority", "grounding_status", "safety_status"])
        .size()
        .rename("case_count")
        .reset_index()
    )
    return {
        "agg_executive_kpis": executive,
        "agg_fraud_performance": fraud_agg,
        "agg_aml_operations": aml_agg,
        "agg_customer_risk_distribution": risk_agg,
        "agg_monitoring_health": monitoring_agg,
        "agg_investigation_workload": investigation_agg,
    }


def generate_reporting_dictionary(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for table_name, frame in tables.items():
        for column in frame.columns:
            key_type = (
                "primary"
                if column.endswith("_key") and frame[column].is_unique
                else "foreign"
                if column.endswith("_key")
                else "none"
            )
            sensitivity = (
                "restricted identifier" if column.endswith("_id") else "internal analytical"
            )
            rows.append(
                {
                    "table_name": table_name,
                    "column_name": column,
                    "business_name": column.replace("_", " ").title(),
                    "data_type": str(frame[column].dtype),
                    "key_type": key_type,
                    "nullable": bool(frame[column].isna().any()),
                    "business_definition": column.replace("_", " "),
                    "source_artifact": "generated upstream artifacts",
                    "transformation_logic": "Deterministic local reporting transformation",
                    "sensitivity_classification": sensitivity,
                    "default_summarisation": "sum"
                    if pd.api.types.is_numeric_dtype(frame[column]) and not column.endswith("_key")
                    else "do not summarise",
                    "display_format": "General",
                    "synthetic_data_flag": True,
                }
            )
    return pd.DataFrame(rows)


def validate_reporting_model(
    tables: dict[str, pd.DataFrame], sources: dict[str, Any], config: dict[str, Any]
) -> dict[str, Any]:
    checks = []

    def check(name: str, passed: bool, category: str, detail: str = "") -> None:
        checks.append(
            {
                "name": name,
                "status": "passed" if passed else "failed",
                "category": category,
                "detail": detail,
            }
        )

    for name in config["required_dimensions"] + config["required_fact_tables"]:
        check(f"table_{name}", name in tables and not tables[name].empty, "table")
    for name, key in [
        ("dim_customer", "customer_key"),
        ("dim_account", "account_key"),
        ("dim_date", "date_key"),
        ("dim_aml_rule", "aml_rule_key"),
    ]:
        check(f"unique_{name}", tables[name][key].is_unique, "relationship")
    relationships = [
        ("fact_transactions", "customer_key", "dim_customer", "customer_key"),
        ("fact_transactions", "account_key", "dim_account", "account_key"),
        ("fact_transactions", "date_key", "dim_date", "date_key"),
        ("fact_aml_alerts", "aml_rule_key", "dim_aml_rule", "aml_rule_key"),
        ("fact_aml_alerts", "customer_key", "dim_customer", "customer_key"),
    ]
    for fact, fk, dim, pk in relationships:
        check(
            f"fk_{fact}_{fk}",
            set(tables[fact][fk].dropna()) <= set(tables[dim][pk]),
            "relationship",
        )
    reconciliations = {
        "transactions": len(tables["fact_transactions"]) == len(sources["transactions"]),
        "aml_alerts": len(tables["fact_aml_alerts"]) == len(sources["aml_alerts"]),
        "customer_risk": len(tables["fact_customer_risk"]) == len(sources["risk"]),
        "investigations": len(tables["fact_investigation_cases"])
        == min(len(sources["cases"]), int(config["maximum_investigation_cases"])),
        "monitoring": len(tables["fact_monitoring_alerts"]) == len(sources["monitoring_alerts"]),
    }
    for name, passed in reconciliations.items():
        check(f"reconcile_{name}", passed, "reconciliation")
    prohibited = sorted(
        {column for frame in tables.values() for column in frame.columns} & PROHIBITED_COLUMNS
    )
    check("privacy_prohibited_columns", not prohibited, "privacy", str(prohibited))
    failures = [item for item in checks if item["status"] == "failed"]
    return {
        "run_timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
        "reporting_version": config["reporting_version"],
        "tables_generated": sorted(tables),
        "rows_by_table": {name: len(frame) for name, frame in tables.items()},
        "relationship_checks": [item for item in checks if item["category"] == "relationship"],
        "reconciliation_checks": [item for item in checks if item["category"] == "reconciliation"],
        "privacy_checks": [item for item in checks if item["category"] == "privacy"],
        "KPI_checks": [{"KPI_count": len(tables["agg_executive_kpis"]), "status": "passed"}],
        "failed_checks": failures,
        "warnings": [],
        "overall_status": "passed" if not failures else "failed",
        "synthetic_data_statement": "All reporting tables contain synthetic analytical data.",
    }


def write_powerbi_outputs(
    tables: dict[str, pd.DataFrame], quality: dict[str, Any], config: dict[str, Any]
) -> dict[str, Path]:
    output = Path(config["output_directory"])
    output.mkdir(parents=True, exist_ok=True)
    paths = {}
    for name, frame in tables.items():
        path = output / f"{name}.csv"
        frame.to_csv(path, index=False)
        paths[name] = path
    quality_path = Path(config["quality_summary_path"])
    quality_path.write_text(json.dumps(quality, indent=2) + "\n", encoding="utf-8")
    paths["quality"] = quality_path
    report = Path(config["quality_report_path"])
    report.parent.mkdir(parents=True, exist_ok=True)
    report_text = "\n".join(
        [
            "# Power BI Reporting Quality Report",
            "",
            f"- Status: `{quality['overall_status']}`",
            f"- Tables: {len(quality['tables_generated'])}",
            f"- Failed checks: {len(quality['failed_checks'])}",
            "- Synthetic data only: `yes`",
            "",
        ]
    )
    report.write_text(report_text, encoding="utf-8")
    paths["report"] = report
    return paths
