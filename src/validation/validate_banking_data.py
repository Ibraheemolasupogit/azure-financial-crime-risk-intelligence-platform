"""Validation checks and report writers for synthetic banking datasets."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from src.data_generation.generate_banking_data import (
    ACCOUNT_FIELDS,
    AML_WATCHLIST_FIELDS,
    CUSTOMER_FIELDS,
    FRAUD_LABEL_FIELDS,
    SESSION_FIELDS,
    TRANSACTION_FIELDS,
)

DEFAULT_MARKDOWN_REPORT_PATH = Path("reports/data_validation_report.md")
DEFAULT_JSON_RESULTS_PATH = Path("outputs/data_validation_results.json")


@dataclass(frozen=True)
class ValidationCheck:
    name: str
    dataset: str
    status: str
    severity: str
    message: str
    category: str


KEY_FIELDS = {
    "customers": ["customer_id"],
    "accounts": ["account_id", "customer_id"],
    "transactions": ["transaction_id", "account_id", "customer_id", "session_id"],
    "device_sessions": ["session_id", "customer_id", "device_id"],
    "fraud_labels": ["transaction_id", "fraud_label"],
    "aml_watchlist": ["watchlist_id", "customer_id"],
}

PRIMARY_KEYS = {
    "customers": "customer_id",
    "accounts": "account_id",
    "transactions": "transaction_id",
    "device_sessions": "session_id",
    "fraud_labels": "transaction_id",
    "aml_watchlist": "watchlist_id",
}

REQUIRED_COLUMNS = {
    "customers": CUSTOMER_FIELDS,
    "accounts": ACCOUNT_FIELDS,
    "transactions": TRANSACTION_FIELDS,
    "device_sessions": SESSION_FIELDS,
    "fraud_labels": FRAUD_LABEL_FIELDS,
    "aml_watchlist": AML_WATCHLIST_FIELDS,
}

CATEGORICAL_VALUES = {
    "customers": {
        "kyc_status": {"Verified", "Pending Review", "Enhanced Due Diligence"},
        "sanctions_screening_status": {"Clear", "Potential Match", "Escalated"},
        "customer_risk_rating": {"Low", "Medium", "High"},
    },
    "accounts": {
        "account_type": {"Current", "Savings", "Credit", "Business"},
        "account_status": {"Active", "Dormant", "Restricted"},
    },
    "transactions": {
        "transaction_status": {"Approved", "Declined", "Reversed"},
        "transaction_type": {"Card Purchase", "Bank Transfer", "Cash Withdrawal", "Direct Debit"},
    },
    "device_sessions": {
        "device_type": {"Mobile", "Desktop", "Tablet"},
        "session_risk_signal": {"Low", "Medium", "Elevated"},
    },
    "fraud_labels": {
        "fraud_label": {0, 1},
        "fraud_typology": {
            "Not Fraud",
            "Account Takeover",
            "Card Not Present Fraud",
            "Synthetic Identity Pattern",
            "Mule Account Activity",
            "Unauthorized Transfer",
        },
    },
    "aml_watchlist": {
        "alert_severity": {"Low", "Medium", "High"},
        "review_status": {"Open", "In Review", "Closed - No Issue", "Escalated"},
    },
}

TIMESTAMP_COLUMNS = {
    "customers": ["date_of_birth", "onboarding_date"],
    "accounts": ["account_open_date"],
    "transactions": ["transaction_timestamp"],
    "device_sessions": ["session_timestamp"],
    "aml_watchlist": ["created_date"],
}


def _check(
    name: str,
    dataset: str,
    passed: bool,
    message: str,
    category: str,
    severity: str = "critical",
) -> ValidationCheck:
    return ValidationCheck(
        name=name,
        dataset=dataset,
        status="passed" if passed else "failed",
        severity=severity,
        message=message,
        category=category,
    )


def validate_required_columns(
    dataset_name: str, dataframe: pd.DataFrame, required_columns: list[str]
) -> list[ValidationCheck]:
    missing = [column for column in required_columns if column not in dataframe.columns]
    return [
        _check(
            "required_columns",
            dataset_name,
            not missing,
            "All required columns are present."
            if not missing
            else f"Missing required columns: {missing}",
            "schema",
        )
    ]


def validate_null_values(
    dataset_name: str, dataframe: pd.DataFrame, key_fields: list[str]
) -> list[ValidationCheck]:
    missing_counts = {
        field: int(dataframe[field].isna().sum())
        for field in key_fields
        if field in dataframe.columns and int(dataframe[field].isna().sum()) > 0
    }
    return [
        _check(
            "key_field_nulls",
            dataset_name,
            not missing_counts,
            "No null values found in key fields."
            if not missing_counts
            else f"Null values found in key fields: {missing_counts}",
            "completeness",
        )
    ]


def validate_duplicate_primary_key(
    dataset_name: str, dataframe: pd.DataFrame, primary_key: str
) -> list[ValidationCheck]:
    if primary_key not in dataframe.columns:
        return [
            _check(
                "duplicate_primary_key",
                dataset_name,
                False,
                f"Primary key column is missing: {primary_key}",
                "uniqueness",
            )
        ]

    duplicates = int(dataframe[primary_key].duplicated().sum())
    return [
        _check(
            "duplicate_primary_key",
            dataset_name,
            duplicates == 0,
            "Primary key values are unique."
            if duplicates == 0
            else f"Found {duplicates} duplicate primary key values.",
            "uniqueness",
        )
    ]


def validate_foreign_key(
    child_dataset: str,
    child_dataframe: pd.DataFrame,
    child_column: str,
    parent_dataset: str,
    parent_dataframe: pd.DataFrame,
    parent_column: str,
) -> list[ValidationCheck]:
    if child_column not in child_dataframe.columns or parent_column not in parent_dataframe.columns:
        return [
            _check(
                f"{child_column}_references_{parent_dataset}",
                child_dataset,
                False,
                f"Cannot validate relationship; missing {child_column} or {parent_column}.",
                "relationship",
            )
        ]

    parent_values = set(parent_dataframe[parent_column].dropna().astype(str))
    child_values = set(child_dataframe[child_column].dropna().astype(str))
    missing_values = sorted(child_values - parent_values)
    preview = missing_values[:5]

    return [
        _check(
            f"{child_column}_references_{parent_dataset}",
            child_dataset,
            not missing_values,
            f"{child_dataset}.{child_column} values all exist in {parent_dataset}.{parent_column}."
            if not missing_values
            else f"Found {len(missing_values)} invalid references. Examples: {preview}",
            "relationship",
        )
    ]


def validate_transaction_amounts(transactions: pd.DataFrame) -> list[ValidationCheck]:
    if "amount" not in transactions.columns:
        return [
            _check(
                "transaction_amount_positive",
                "transactions",
                False,
                "Missing amount column.",
                "validity",
            )
        ]

    numeric_amounts = pd.to_numeric(transactions["amount"], errors="coerce")
    invalid_count = int((numeric_amounts.isna() | (numeric_amounts <= 0)).sum())
    return [
        _check(
            "transaction_amount_positive",
            "transactions",
            invalid_count == 0,
            "All transaction amounts are numeric and positive."
            if invalid_count == 0
            else f"Found {invalid_count} transactions with invalid amounts.",
            "validity",
        )
    ]


def validate_timestamps(
    dataset_name: str, dataframe: pd.DataFrame, timestamp_columns: list[str]
) -> list[ValidationCheck]:
    checks: list[ValidationCheck] = []
    for column in timestamp_columns:
        if column not in dataframe.columns:
            checks.append(
                _check(
                    f"{column}_timestamp_parseable",
                    dataset_name,
                    False,
                    f"Missing timestamp/date column: {column}",
                    "validity",
                )
            )
            continue

        parsed = pd.to_datetime(dataframe[column], errors="coerce")
        invalid_count = int(parsed.isna().sum())
        checks.append(
            _check(
                f"{column}_timestamp_parseable",
                dataset_name,
                invalid_count == 0,
                f"All values in {column} are parseable."
                if invalid_count == 0
                else f"Found {invalid_count} unparseable values in {column}.",
                "validity",
            )
        )
    return checks


def validate_categorical_values(
    dataset_name: str, dataframe: pd.DataFrame, allowed_values: dict[str, set[Any]]
) -> list[ValidationCheck]:
    checks: list[ValidationCheck] = []
    for column, allowed in allowed_values.items():
        if column not in dataframe.columns:
            checks.append(
                _check(
                    f"{column}_allowed_values",
                    dataset_name,
                    False,
                    f"Missing categorical column: {column}",
                    "validity",
                )
            )
            continue

        observed = set(dataframe[column].dropna().tolist())
        invalid_values = sorted(str(value) for value in observed if value not in allowed)
        checks.append(
            _check(
                f"{column}_allowed_values",
                dataset_name,
                not invalid_values,
                f"All values in {column} are within the expected domain."
                if not invalid_values
                else f"Unexpected values in {column}: {invalid_values}",
                "validity",
            )
        )
    return checks


def validate_all_datasets(datasets: dict[str, pd.DataFrame]) -> dict[str, Any]:
    checks: list[ValidationCheck] = []

    for dataset_name, required_columns in REQUIRED_COLUMNS.items():
        dataframe = datasets[dataset_name]
        checks.extend(validate_required_columns(dataset_name, dataframe, required_columns))
        checks.extend(validate_null_values(dataset_name, dataframe, KEY_FIELDS[dataset_name]))
        checks.extend(
            validate_duplicate_primary_key(
                dataset_name, dataframe, PRIMARY_KEYS[dataset_name]
            )
        )
        checks.extend(
            validate_timestamps(dataset_name, dataframe, TIMESTAMP_COLUMNS.get(dataset_name, []))
        )
        checks.extend(
            validate_categorical_values(
                dataset_name, dataframe, CATEGORICAL_VALUES.get(dataset_name, {})
            )
        )

    checks.extend(
        validate_foreign_key(
            "accounts",
            datasets["accounts"],
            "customer_id",
            "customers",
            datasets["customers"],
            "customer_id",
        )
    )
    checks.extend(
        validate_foreign_key(
            "transactions",
            datasets["transactions"],
            "account_id",
            "accounts",
            datasets["accounts"],
            "account_id",
        )
    )
    checks.extend(
        validate_foreign_key(
            "transactions",
            datasets["transactions"],
            "customer_id",
            "customers",
            datasets["customers"],
            "customer_id",
        )
    )
    checks.extend(
        validate_foreign_key(
            "transactions",
            datasets["transactions"],
            "session_id",
            "device_sessions",
            datasets["device_sessions"],
            "session_id",
        )
    )
    checks.extend(
        validate_foreign_key(
            "device_sessions",
            datasets["device_sessions"],
            "customer_id",
            "customers",
            datasets["customers"],
            "customer_id",
        )
    )
    checks.extend(
        validate_foreign_key(
            "fraud_labels",
            datasets["fraud_labels"],
            "transaction_id",
            "transactions",
            datasets["transactions"],
            "transaction_id",
        )
    )
    checks.extend(
        validate_foreign_key(
            "aml_watchlist",
            datasets["aml_watchlist"],
            "customer_id",
            "customers",
            datasets["customers"],
            "customer_id",
        )
    )
    checks.extend(validate_transaction_amounts(datasets["transactions"]))

    check_dicts = [asdict(check) for check in checks]
    failed_checks = [check for check in check_dicts if check["status"] == "failed"]
    warnings = [check for check in failed_checks if check["severity"] == "warning"]
    critical_failures = [check for check in failed_checks if check["severity"] == "critical"]
    relationship_checks = [check for check in check_dicts if check["category"] == "relationship"]

    return {
        "validation_run_timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
        "datasets_checked": sorted(datasets.keys()),
        "row_counts": {name: int(len(dataframe)) for name, dataframe in datasets.items()},
        "overall_status": "passed" if not critical_failures else "failed",
        "passed_checks": [check for check in check_dicts if check["status"] == "passed"],
        "failed_checks": failed_checks,
        "warnings": warnings,
        "relationship_checks": relationship_checks,
        "checks": check_dicts,
    }


def write_validation_json(report: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)
        file.write("\n")


def write_validation_markdown(report: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Data Validation Report",
        "",
        f"- Validation run timestamp: `{report['validation_run_timestamp']}`",
        f"- Overall validation status: `{report['overall_status']}`",
        f"- Datasets checked: {', '.join(report['datasets_checked'])}",
        "",
        "## Row Counts",
        "",
        "| Dataset | Rows |",
        "| --- | ---: |",
    ]

    for dataset_name, row_count in report["row_counts"].items():
        lines.append(f"| {dataset_name} | {row_count} |")

    lines.extend(
        [
            "",
            "## Check Summary",
            "",
            f"- Passed checks: {len(report['passed_checks'])}",
            f"- Failed checks: {len(report['failed_checks'])}",
            f"- Warnings: {len(report['warnings'])}",
            "",
            "## Relationship Checks",
            "",
            "| Dataset | Check | Status | Message |",
            "| --- | --- | --- | --- |",
        ]
    )

    for check in report["relationship_checks"]:
        lines.append(
            f"| {check['dataset']} | {check['name']} | {check['status']} | {check['message']} |"
        )

    lines.extend(["", "## Failed Checks", ""])
    if report["failed_checks"]:
        lines.extend(
            f"- `{check['dataset']}` `{check['name']}`: {check['message']}"
            for check in report["failed_checks"]
        )
    else:
        lines.append("No failed checks.")

    lines.extend(["", "## Warnings", ""])
    if report["warnings"]:
        lines.extend(
            f"- `{check['dataset']}` `{check['name']}`: {check['message']}"
            for check in report["warnings"]
        )
    else:
        lines.append("No warnings.")

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_validation_outputs(
    report: dict[str, Any],
    markdown_path: Path = DEFAULT_MARKDOWN_REPORT_PATH,
    json_path: Path = DEFAULT_JSON_RESULTS_PATH,
) -> None:
    write_validation_markdown(report, markdown_path)
    write_validation_json(report, json_path)
