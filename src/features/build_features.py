"""Build deterministic, model-ready features from validated synthetic banking data."""

from __future__ import annotations

import json
from collections import Counter, defaultdict, deque
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

DEFAULT_FEATURE_CONFIG_PATH = Path("configs/feature_config.yaml")
DEFAULT_REPORT_PATH = Path("reports/feature_engineering_report.md")
DEFAULT_SUMMARY_PATH = Path("outputs/feature_engineering_summary.json")

TRANSACTION_REQUIRED_COLUMNS = {
    "transaction_id",
    "account_id",
    "customer_id",
    "transaction_timestamp",
    "channel",
    "merchant_category",
    "merchant_country",
    "amount",
    "is_cross_border",
    "transaction_status",
    "device_id",
    "session_id",
}

DATASET_REQUIRED_COLUMNS = {
    "customers": {
        "customer_id",
        "country",
        "onboarding_date",
        "kyc_status",
        "pep_flag",
        "sanctions_screening_status",
    },
    "accounts": {
        "account_id",
        "customer_id",
        "account_type",
        "account_open_date",
        "account_status",
    },
    "transactions": TRANSACTION_REQUIRED_COLUMNS,
    "device_sessions": {
        "session_id",
        "customer_id",
        "device_id",
        "ip_country",
        "session_risk_signal",
    },
    "fraud_labels": {"transaction_id", "fraud_label"},
    "aml_watchlist": {"customer_id"},
}

LABEL_COLUMNS = {"fraud_label", "fraud_typology", "label_confidence", "label_source"}


def _require_columns(dataframe: pd.DataFrame, required: set[str], dataset_name: str) -> None:
    missing = sorted(required - set(dataframe.columns))
    if missing:
        raise ValueError(f"{dataset_name} is missing required columns: {missing}")


def _as_bool(series: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(series):
        return series.fillna(False)
    return series.astype(str).str.lower().map({"true": True, "false": False}).fillna(False)


def _validate_config(config: dict[str, Any]) -> None:
    required = {
        "reference_timestamp",
        "velocity_window_hours",
        "behaviour_window_days",
        "night_start_hour",
        "night_end_hour",
        "rapid_transaction_minutes",
        "high_value_transaction_threshold",
        "high_risk_channels",
        "high_risk_merchant_categories",
        "high_risk_countries",
        "include_label_columns",
    }
    missing = sorted(required - set(config))
    if missing:
        raise ValueError(f"Feature configuration is missing required settings: {missing}")
    if int(config["velocity_window_hours"]) <= 0 or int(config["behaviour_window_days"]) <= 0:
        raise ValueError("Feature window settings must be positive.")
    if int(config["rapid_transaction_minutes"]) <= 0:
        raise ValueError("rapid_transaction_minutes must be positive.")
    if pd.isna(pd.to_datetime(config["reference_timestamp"], errors="coerce")):
        raise ValueError("reference_timestamp must be parseable.")


def prepare_transaction_timestamps(transactions: pd.DataFrame) -> pd.DataFrame:
    """Parse timestamps and return transactions in stable chronological order."""
    _require_columns(transactions, TRANSACTION_REQUIRED_COLUMNS, "transactions")
    prepared = transactions.copy()
    prepared["transaction_timestamp"] = pd.to_datetime(
        prepared["transaction_timestamp"], errors="coerce"
    )
    invalid = int(prepared["transaction_timestamp"].isna().sum())
    if invalid:
        raise ValueError(f"transactions contains {invalid} unparseable transaction timestamps.")
    prepared["amount"] = pd.to_numeric(prepared["amount"], errors="coerce")
    if prepared["amount"].isna().any() or (prepared["amount"] <= 0).any():
        raise ValueError("transactions.amount must contain positive numeric values.")
    return prepared.sort_values(
        ["transaction_timestamp", "transaction_id"], kind="stable"
    ).reset_index(drop=True)


def create_temporal_and_monetary_features(
    transactions: pd.DataFrame, config: dict[str, Any]
) -> pd.DataFrame:
    """Create timestamp, amount, and prior-average transaction features."""
    featured = transactions.copy()
    timestamp = featured["transaction_timestamp"]
    featured["transaction_hour"] = timestamp.dt.hour.astype("int64")
    featured["transaction_day_of_week"] = timestamp.dt.dayofweek.astype("int64")
    featured["is_weekend"] = (featured["transaction_day_of_week"] >= 5).astype("int64")
    start_hour = int(config["night_start_hour"])
    end_hour = int(config["night_end_hour"])
    if start_hour > end_hour:
        night = (featured["transaction_hour"] >= start_hour) | (
            featured["transaction_hour"] < end_hour
        )
    else:
        night = featured["transaction_hour"].between(start_hour, end_hour, inclusive="left")
    featured["is_night_transaction"] = night.astype("int64")
    featured["log_transaction_amount"] = np.log1p(featured["amount"])
    featured["high_value_transaction_flag"] = (
        featured["amount"] >= float(config["high_value_transaction_threshold"])
    ).astype("int64")

    for entity, output_name in (
        ("account_id", "amount_vs_account_average"),
        ("customer_id", "amount_vs_customer_average"),
    ):
        prior_sum = featured.groupby(entity, sort=False)["amount"].cumsum() - featured["amount"]
        prior_count = featured.groupby(entity, sort=False).cumcount()
        prior_average = prior_sum.div(prior_count.replace(0, np.nan))
        featured[output_name] = featured["amount"].div(prior_average).replace(
            [np.inf, -np.inf], np.nan
        ).fillna(1.0)
    return featured


def _historical_window_metrics(
    dataframe: pd.DataFrame,
    entity_column: str,
    window: timedelta,
    distinct_columns: tuple[str, ...] = (),
) -> pd.DataFrame:
    """Calculate prior-only rolling metrics for each entity."""
    count_result = pd.Series(0, index=dataframe.index, dtype="int64")
    amount_result = pd.Series(0.0, index=dataframe.index, dtype="float64")
    distinct_results = {
        column: pd.Series(0, index=dataframe.index, dtype="int64")
        for column in distinct_columns
    }

    for _, group in dataframe.groupby(entity_column, sort=False):
        active: deque[tuple[int, pd.Timestamp, float, dict[str, Any]]] = deque()
        counters = {column: Counter() for column in distinct_columns}
        running_amount = 0.0
        for index, row in group.iterrows():
            current_time = row["transaction_timestamp"]
            cutoff = current_time - window
            while active and active[0][1] < cutoff:
                _, _, old_amount, old_values = active.popleft()
                running_amount -= old_amount
                for column, value in old_values.items():
                    counters[column][value] -= 1
                    if counters[column][value] == 0:
                        del counters[column][value]

            count_result.at[index] = len(active)
            amount_result.at[index] = max(running_amount, 0.0)
            for column in distinct_columns:
                distinct_results[column].at[index] = len(counters[column])

            values = {column: row[column] for column in distinct_columns}
            active.append((index, current_time, float(row["amount"]), values))
            running_amount += float(row["amount"])
            for column, value in values.items():
                counters[column][value] += 1

    output = pd.DataFrame({"count": count_result, "amount": amount_result})
    for column, result in distinct_results.items():
        output[f"distinct_{column}"] = result
    return output


def create_behavioural_velocity_features(
    transactions: pd.DataFrame, config: dict[str, Any]
) -> pd.DataFrame:
    """Create prior-only customer/account velocity and recent-behaviour features."""
    featured = transactions.copy()
    velocity_window = timedelta(hours=int(config["velocity_window_hours"]))
    behaviour_window = timedelta(days=int(config["behaviour_window_days"]))

    customer_velocity = _historical_window_metrics(
        featured, "customer_id", velocity_window
    )
    account_velocity = _historical_window_metrics(featured, "account_id", velocity_window)
    behaviour = _historical_window_metrics(
        featured,
        "customer_id",
        behaviour_window,
        distinct_columns=("merchant_country", "merchant_category"),
    )
    featured["transaction_count_customer_24h"] = customer_velocity["count"]
    featured["transaction_amount_customer_24h"] = customer_velocity["amount"]
    featured["transaction_count_account_24h"] = account_velocity["count"]
    featured["transaction_amount_account_24h"] = account_velocity["amount"]
    featured["distinct_countries_customer_7d"] = behaviour[
        "distinct_merchant_country"
    ]
    featured["distinct_merchants_customer_7d"] = behaviour[
        "distinct_merchant_category"
    ]

    cross_border = _as_bool(featured["is_cross_border"]).astype("int64")
    failed = featured["transaction_status"].ne("Approved").astype("int64")
    featured["cross_border_transaction_count_7d"] = _prior_conditional_count(
        featured, "customer_id", cross_border, behaviour_window
    )
    featured["failed_transaction_count_24h"] = _prior_conditional_count(
        featured, "customer_id", failed, velocity_window
    )

    prior_time = featured.groupby("customer_id", sort=False)["transaction_timestamp"].shift()
    seconds_since_prior = (featured["transaction_timestamp"] - prior_time).dt.total_seconds()
    rapid_seconds = int(config["rapid_transaction_minutes"]) * 60
    featured["rapid_transaction_flag"] = seconds_since_prior.le(rapid_seconds).fillna(False).astype(
        "int64"
    )
    featured["transaction_velocity_score"] = (
        np.log1p(featured["transaction_count_customer_24h"])
        + np.log1p(featured["transaction_amount_customer_24h"] / 100.0)
        + featured["rapid_transaction_flag"]
    )
    return featured


def _prior_conditional_count(
    dataframe: pd.DataFrame,
    entity_column: str,
    condition: pd.Series,
    window: timedelta,
) -> pd.Series:
    result = pd.Series(0, index=dataframe.index, dtype="int64")
    for _, group in dataframe.groupby(entity_column, sort=False):
        active: deque[tuple[pd.Timestamp, int]] = deque()
        running_count = 0
        for index in group.index:
            current_time = dataframe.at[index, "transaction_timestamp"]
            cutoff = current_time - window
            while active and active[0][0] < cutoff:
                _, old_value = active.popleft()
                running_count -= old_value
            result.at[index] = running_count
            value = int(condition.at[index])
            active.append((current_time, value))
            running_count += value
    return result


def create_device_and_session_risk_features(
    transactions: pd.DataFrame,
    device_sessions: pd.DataFrame,
    customers: pd.DataFrame,
) -> pd.DataFrame:
    """Add session risk, customer-country mismatch, and device novelty signals."""
    _require_columns(
        device_sessions, DATASET_REQUIRED_COLUMNS["device_sessions"], "device_sessions"
    )
    _require_columns(customers, DATASET_REQUIRED_COLUMNS["customers"], "customers")
    session_context = device_sessions[
        ["session_id", "ip_country", "session_risk_signal"]
    ].drop_duplicates("session_id")
    customer_context = customers[["customer_id", "country"]].rename(
        columns={"country": "customer_country"}
    )
    featured = transactions.merge(
        session_context, on="session_id", how="left", validate="many_to_one"
    )
    featured = featured.merge(
        customer_context, on="customer_id", how="left", validate="many_to_one"
    )
    featured["risky_session_flag"] = featured["session_risk_signal"].isin(
        ["Medium", "Elevated"]
    ).astype("int64")
    featured["country_mismatch_flag"] = (
        featured["ip_country"].ne(featured["customer_country"])
        | featured["merchant_country"].ne(featured["customer_country"])
    ).astype("int64")

    seen_devices: dict[str, set[str]] = defaultdict(set)
    new_device_flags: list[int] = []
    for row in featured.itertuples(index=False):
        customer_devices = seen_devices[str(row.customer_id)]
        device = str(row.device_id)
        new_device_flags.append(int(device not in customer_devices))
        customer_devices.add(device)
    featured["new_device_flag"] = new_device_flags
    return featured


def create_geographic_and_cross_border_features(
    transactions: pd.DataFrame, config: dict[str, Any]
) -> pd.DataFrame:
    """Encode cross-border and configured high-risk-country signals."""
    featured = transactions.copy()
    featured["is_cross_border"] = _as_bool(featured["is_cross_border"]).astype("int64")
    featured["high_risk_country_flag"] = featured["merchant_country"].isin(
        set(config["high_risk_countries"])
    ).astype("int64")
    return featured


def create_merchant_and_channel_features(
    transactions: pd.DataFrame, config: dict[str, Any]
) -> pd.DataFrame:
    """Encode configured high-risk merchant and channel indicators."""
    featured = transactions.copy()
    featured["high_risk_channel_flag"] = featured["channel"].isin(
        set(config["high_risk_channels"])
    ).astype("int64")
    featured["high_risk_merchant_category_flag"] = featured["merchant_category"].isin(
        set(config["high_risk_merchant_categories"])
    ).astype("int64")
    return featured


def create_transaction_features(
    transactions: pd.DataFrame,
    device_sessions: pd.DataFrame,
    customers: pd.DataFrame,
    config: dict[str, Any],
) -> pd.DataFrame:
    """Build the transaction feature table without supervised label columns."""
    _validate_config(config)
    featured = prepare_transaction_timestamps(transactions)
    featured = create_temporal_and_monetary_features(featured, config)
    featured = create_behavioural_velocity_features(featured, config)
    featured = create_device_and_session_risk_features(featured, device_sessions, customers)
    featured = create_geographic_and_cross_border_features(featured, config)
    featured = create_merchant_and_channel_features(featured, config)
    return featured.sort_values("transaction_id", kind="stable").reset_index(drop=True)


def join_fraud_labels(
    transaction_features: pd.DataFrame, fraud_labels: pd.DataFrame
) -> pd.DataFrame:
    """Join outcomes only after predictive transaction features are complete."""
    _require_columns(fraud_labels, DATASET_REQUIRED_COLUMNS["fraud_labels"], "fraud_labels")
    label_columns = [
        column
        for column in [
            "transaction_id",
            "fraud_label",
            "fraud_typology",
            "label_confidence",
            "label_source",
        ]
        if column in fraud_labels.columns
    ]
    return transaction_features.merge(
        fraud_labels[label_columns], on="transaction_id", how="left", validate="one_to_one"
    )


def create_account_level_aggregates(
    accounts: pd.DataFrame, transaction_features: pd.DataFrame, config: dict[str, Any]
) -> pd.DataFrame:
    """Build one descriptive feature row per account."""
    _require_columns(accounts, DATASET_REQUIRED_COLUMNS["accounts"], "accounts")
    reference = pd.Timestamp(config["reference_timestamp"])
    transactions = transaction_features.copy()
    transactions["failed_flag"] = transactions["transaction_status"].ne("Approved").astype(int)
    grouped = transactions.groupby("account_id", sort=True)
    aggregates = grouped.agg(
        transaction_count=("transaction_id", "count"),
        total_transaction_amount=("amount", "sum"),
        average_transaction_amount=("amount", "mean"),
        maximum_transaction_amount=("amount", "max"),
        failed_transaction_count=("failed_flag", "sum"),
        cross_border_transaction_count=("is_cross_border", "sum"),
        unique_merchant_country_count=("merchant_country", "nunique"),
        unique_device_count=("device_id", "nunique"),
    ).reset_index()
    account_columns = [
        "account_id",
        "customer_id",
        "account_open_date",
        "account_status",
        "account_type",
    ]
    output = accounts[account_columns].merge(
        aggregates, on="account_id", how="left", validate="one_to_one"
    )
    numeric_aggregate_columns = list(aggregates.columns.drop("account_id"))
    output[numeric_aggregate_columns] = output[numeric_aggregate_columns].fillna(0)
    opened = pd.to_datetime(output["account_open_date"], errors="coerce")
    if opened.isna().any():
        raise ValueError("accounts contains unparseable account_open_date values.")
    output["account_age_days"] = (reference - opened).dt.days.clip(lower=0)
    output["account_status_encoded"] = output["account_status"].map(
        {"Active": 0, "Dormant": 1, "Restricted": 2}
    ).astype("int64")
    output["account_type_encoded"] = output["account_type"].map(
        {"Current": 0, "Savings": 1, "Credit": 2, "Business": 3}
    ).astype("int64")
    return output.sort_values("account_id", kind="stable").reset_index(drop=True)


def create_customer_level_aggregates(
    customers: pd.DataFrame,
    accounts: pd.DataFrame,
    transaction_features: pd.DataFrame,
    device_sessions: pd.DataFrame,
    fraud_labels: pd.DataFrame,
    aml_watchlist: pd.DataFrame,
    config: dict[str, Any],
) -> pd.DataFrame:
    """Build behavioural, KYC, AML, and historical-outcome customer features."""
    _require_columns(customers, DATASET_REQUIRED_COLUMNS["customers"], "customers")
    _require_columns(aml_watchlist, DATASET_REQUIRED_COLUMNS["aml_watchlist"], "aml_watchlist")
    reference = pd.Timestamp(config["reference_timestamp"])

    account_work = accounts.copy()
    account_work["active_flag"] = account_work["account_status"].eq("Active").astype(int)
    account_work["account_open_date"] = pd.to_datetime(
        account_work["account_open_date"], errors="coerce"
    )
    account_aggregates = account_work.groupby("customer_id", sort=True).agg(
        number_of_accounts=("account_id", "count"),
        active_account_count=("active_flag", "sum"),
        earliest_account_open_date=("account_open_date", "min"),
    ).reset_index()
    account_aggregates["account_tenure_days"] = (
        reference - account_aggregates.pop("earliest_account_open_date")
    ).dt.days.clip(lower=0)

    transaction_work = transaction_features.copy()
    transaction_work["failed_flag"] = (
        transaction_work["transaction_status"].ne("Approved").astype(int)
    )
    transaction_group = transaction_work.groupby("customer_id", sort=True)
    transaction_aggregates = transaction_group.agg(
        total_transaction_count=("transaction_id", "count"),
        total_transaction_amount=("amount", "sum"),
        average_transaction_amount=("amount", "mean"),
        maximum_transaction_amount=("amount", "max"),
        cross_border_count=("is_cross_border", "sum"),
        failed_transaction_count=("failed_flag", "sum"),
        night_transaction_count=("is_night_transaction", "sum"),
        unique_merchant_country_count=("merchant_country", "nunique"),
        unique_device_count=("device_id", "nunique"),
        new_device_transaction_count=("new_device_flag", "sum"),
    ).reset_index()
    denominator = transaction_aggregates["total_transaction_count"].replace(0, np.nan)
    transaction_aggregates["cross_border_ratio"] = (
        transaction_aggregates.pop("cross_border_count") / denominator
    ).fillna(0.0)
    transaction_aggregates["failed_transaction_ratio"] = (
        transaction_aggregates.pop("failed_transaction_count") / denominator
    ).fillna(0.0)
    transaction_aggregates["night_transaction_ratio"] = (
        transaction_aggregates.pop("night_transaction_count") / denominator
    ).fillna(0.0)

    session_work = device_sessions.copy()
    session_work["risky_session"] = session_work["session_risk_signal"].isin(
        ["Medium", "Elevated"]
    ).astype(int)
    session_aggregates = session_work.groupby("customer_id", sort=True).agg(
        risky_session_count=("risky_session", "sum")
    ).reset_index()

    outcomes = transaction_work[["transaction_id", "customer_id"]].merge(
        fraud_labels[["transaction_id", "fraud_label"]],
        on="transaction_id",
        how="left",
        validate="one_to_one",
    )
    outcomes["fraud_label"] = pd.to_numeric(outcomes["fraud_label"], errors="coerce").fillna(0)
    fraud_aggregates = outcomes.groupby("customer_id", sort=True).agg(
        historical_fraud_count=("fraud_label", "sum"),
        historical_fraud_rate=("fraud_label", "mean"),
    ).reset_index()

    watchlist_customers = set(aml_watchlist["customer_id"].astype(str))
    output = customers[
        [
            "customer_id",
            "onboarding_date",
            "pep_flag",
            "kyc_status",
            "sanctions_screening_status",
        ]
    ].copy()
    aggregate_tables = (
        account_aggregates,
        transaction_aggregates,
        session_aggregates,
        fraud_aggregates,
    )
    for aggregate in aggregate_tables:
        output = output.merge(aggregate, on="customer_id", how="left", validate="one_to_one")

    onboarding = pd.to_datetime(output["onboarding_date"], errors="coerce")
    if onboarding.isna().any():
        raise ValueError("customers contains unparseable onboarding_date values.")
    output["customer_tenure_days"] = (reference - onboarding).dt.days.clip(lower=0)
    output["aml_watchlist_flag"] = (
        output["customer_id"].astype(str).isin(watchlist_customers).astype(int)
    )
    output["pep_flag_encoded"] = _as_bool(output["pep_flag"]).astype(int)
    output["kyc_status_encoded"] = output["kyc_status"].map(
        {"Verified": 0, "Pending Review": 1, "Enhanced Due Diligence": 2}
    ).astype("int64")
    output["sanctions_screening_flag"] = (
        output["sanctions_screening_status"].ne("Clear").astype(int)
    )
    numeric_columns = output.select_dtypes(include="number").columns
    output[numeric_columns] = output[numeric_columns].fillna(0)
    return output.sort_values("customer_id", kind="stable").reset_index(drop=True)


def get_predictive_transaction_columns(transaction_features: pd.DataFrame) -> list[str]:
    """Return transaction columns eligible as predictive inputs, excluding outcomes."""
    return [column for column in transaction_features.columns if column not in LABEL_COLUMNS]


def build_final_feature_datasets(
    datasets: dict[str, pd.DataFrame], config: dict[str, Any]
) -> dict[str, pd.DataFrame]:
    """Build transaction, account, customer, and dictionary feature tables."""
    _validate_config(config)
    missing_datasets = sorted(DATASET_REQUIRED_COLUMNS.keys() - datasets.keys())
    if missing_datasets:
        raise ValueError(f"Missing input datasets: {missing_datasets}")
    for name, required in DATASET_REQUIRED_COLUMNS.items():
        _require_columns(datasets[name], required, name)

    transaction_predictors = create_transaction_features(
        datasets["transactions"], datasets["device_sessions"], datasets["customers"], config
    )
    transaction_output = (
        join_fraud_labels(transaction_predictors, datasets["fraud_labels"])
        if bool(config["include_label_columns"])
        else transaction_predictors
    )
    account_features = create_account_level_aggregates(
        datasets["accounts"], transaction_predictors, config
    )
    customer_features = create_customer_level_aggregates(
        datasets["customers"],
        datasets["accounts"],
        transaction_predictors,
        datasets["device_sessions"],
        datasets["fraud_labels"],
        datasets["aml_watchlist"],
        config,
    )
    feature_dictionary = build_feature_dictionary(
        transaction_output, account_features, customer_features
    )
    return {
        "transaction_features": transaction_output,
        "account_features": account_features,
        "customer_features": customer_features,
        "feature_dictionary": feature_dictionary,
    }


def _feature_metadata(feature_name: str, table: str) -> dict[str, str]:
    label = feature_name in LABEL_COLUMNS or feature_name.startswith("historical_fraud_")
    if label:
        category = "label"
    elif any(
        token in feature_name
        for token in ("hour", "day_of_week", "weekend", "night", "tenure", "age_days")
    ):
        category = "temporal"
    elif any(token in feature_name for token in ("amount", "value")):
        category = "monetary"
    elif any(token in feature_name for token in ("country", "cross_border")):
        category = "geographic"
    elif any(token in feature_name for token in ("device", "session")):
        category = "device"
    elif any(token in feature_name for token in ("24h", "7d", "velocity", "rapid")):
        category = "velocity"
    elif any(token in feature_name for token in ("kyc", "pep", "sanctions")):
        category = "KYC"
    elif "aml" in feature_name or "watchlist" in feature_name:
        category = "AML"
    elif table == "account_features" or "account" in feature_name:
        category = "account"
    else:
        category = "behavioural"

    source = "derived"
    if label:
        source = "fraud_labels"
    elif category == "KYC":
        source = "customers"
    elif category == "AML":
        source = "aml_watchlist"
    elif category == "device":
        source = "transactions;device_sessions"
    return {
        "category": category,
        "description": feature_name.replace("_", " ").capitalize() + ".",
        "source_dataset": source,
        "leakage_risk": "high - outcome only" if label else "low - prior-only or static",
        "intended_use": "outcome analysis only" if label else "predictive modelling and analytics",
    }


def build_feature_dictionary(
    transaction_features: pd.DataFrame,
    account_features: pd.DataFrame,
    customer_features: pd.DataFrame,
) -> pd.DataFrame:
    """Create a machine-readable catalogue of all output columns."""
    rows: list[dict[str, str]] = []
    for table_name, dataframe in (
        ("transaction_features", transaction_features),
        ("account_features", account_features),
        ("customer_features", customer_features),
    ):
        for column in dataframe.columns:
            rows.append(
                {
                    "feature_name": column,
                    "feature_table": table_name,
                    "data_type": str(dataframe[column].dtype),
                    **_feature_metadata(column, table_name),
                }
            )
    return pd.DataFrame(rows)


def write_feature_outputs(
    feature_datasets: dict[str, pd.DataFrame], output_dir: Path | str
) -> dict[str, Path]:
    """Write all feature tables to stable CSV paths."""
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    output_paths = {
        "transaction_features": destination / "transaction_features.csv",
        "account_features": destination / "account_features.csv",
        "customer_features": destination / "customer_features.csv",
        "feature_dictionary": destination / "feature_dictionary.csv",
    }
    for name, path in output_paths.items():
        feature_datasets[name].to_csv(path, index=False)
    return output_paths


def build_feature_summary(
    input_datasets: dict[str, pd.DataFrame], feature_datasets: dict[str, pd.DataFrame]
) -> dict[str, Any]:
    """Build report metrics for feature quality and leakage controls."""
    feature_tables = {
        name: dataframe
        for name, dataframe in feature_datasets.items()
        if name != "feature_dictionary"
    }
    duplicate_keys = {
        "transaction_features.transaction_id": int(
            feature_tables["transaction_features"]["transaction_id"].duplicated().sum()
        ),
        "account_features.account_id": int(
            feature_tables["account_features"]["account_id"].duplicated().sum()
        ),
        "customer_features.customer_id": int(
            feature_tables["customer_features"]["customer_id"].duplicated().sum()
        ),
    }
    missing_values = {
        table: {
            column: int(count)
            for column, count in dataframe.isna().sum().items()
            if int(count) > 0
        }
        for table, dataframe in feature_tables.items()
    }
    dictionary = feature_datasets["feature_dictionary"]
    categories = {
        str(category): int(count)
        for category, count in dictionary["category"].value_counts().sort_index().items()
    }
    has_duplicate_keys = any(duplicate_keys.values())
    return {
        "run_timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
        "input_row_counts": {name: int(len(df)) for name, df in input_datasets.items()},
        "output_row_counts": {name: int(len(df)) for name, df in feature_tables.items()},
        "feature_counts": {name: int(len(df.columns)) for name, df in feature_tables.items()},
        "missing_value_summary": missing_values,
        "duplicate_key_summary": duplicate_keys,
        "feature_categories": categories,
        "label_separation_statement": (
            "Fraud labels are joined after predictive transaction features are computed and are "
            "excluded from the predictive transaction column list."
        ),
        "leakage_controls": [
            "Transaction windows are chronological and exclude the current transaction.",
            "Prior entity averages exclude the current transaction.",
            "Device novelty is based only on devices seen earlier in transaction order.",
            "Fraud outcome fields are explicitly classified as label features.",
            "Customer historical fraud fields are outcome features for retrospective risk "
            "analysis, not transaction prediction.",
        ],
        "overall_status": "failed" if has_duplicate_keys else "passed",
    }


def write_feature_report(summary: dict[str, Any], output_path: Path) -> None:
    """Write the human-readable feature engineering report."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Feature Engineering Report",
        "",
        f"- Run timestamp: `{summary['run_timestamp']}`",
        f"- Overall status: `{summary['overall_status']}`",
        "- Synthetic data only: `yes`",
        "",
        "## Input Row Counts",
        "",
        "| Dataset | Rows |",
        "| --- | ---: |",
    ]
    lines.extend(f"| {name} | {count} |" for name, count in summary["input_row_counts"].items())
    lines.extend(
        [
            "",
            "## Output Feature Tables",
            "",
            "| Table | Rows | Columns |",
            "| --- | ---: | ---: |",
        ]
    )
    for name, count in summary["output_row_counts"].items():
        lines.append(f"| {name} | {count} | {summary['feature_counts'][name]} |")
    lines.extend(
        ["", "## Feature Categories", "", "| Category | Features |", "| --- | ---: |"]
    )
    lines.extend(f"| {name} | {count} |" for name, count in summary["feature_categories"].items())
    lines.extend(["", "## Quality Summary", ""])
    missing_json = json.dumps(summary["missing_value_summary"], sort_keys=True)
    duplicate_json = json.dumps(summary["duplicate_key_summary"], sort_keys=True)
    lines.append(f"- Missing values: `{missing_json}`")
    lines.append(f"- Duplicate keys: `{duplicate_json}`")
    lines.extend(["", "## Label Separation", "", summary["label_separation_statement"]])
    lines.extend(["", "## Leakage Controls", ""])
    lines.extend(f"- {control}" for control in summary["leakage_controls"])
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_feature_summary_json(summary: dict[str, Any], output_path: Path) -> None:
    """Write the machine-readable feature engineering summary."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


def write_feature_quality_outputs(
    summary: dict[str, Any],
    report_path: Path = DEFAULT_REPORT_PATH,
    summary_path: Path = DEFAULT_SUMMARY_PATH,
) -> None:
    """Write both feature engineering quality artifacts."""
    write_feature_report(summary, report_path)
    write_feature_summary_json(summary, summary_path)
