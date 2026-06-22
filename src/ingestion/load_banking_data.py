"""Local loaders for synthetic banking datasets."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.data_generation.generate_banking_data import (
    ACCOUNT_FIELDS,
    AML_WATCHLIST_FIELDS,
    CUSTOMER_FIELDS,
    FRAUD_LABEL_FIELDS,
    SESSION_FIELDS,
    TRANSACTION_FIELDS,
)

DEFAULT_DATA_DIR = Path("data/raw")


def _resolve_dataset_path(data_dir: Path, filename: str) -> Path:
    path = data_dir / filename
    if not path.exists():
        raise FileNotFoundError(
            f"Required dataset file not found: {path}. "
            "Run `python3 scripts/generate_synthetic_data.py` first."
        )
    return path


def _normalise_columns(dataframe: pd.DataFrame, expected_columns: list[str]) -> pd.DataFrame:
    dataframe = dataframe.copy()
    dataframe.columns = [str(column).strip() for column in dataframe.columns]
    ordered_columns = [column for column in expected_columns if column in dataframe.columns]
    extra_columns = [column for column in dataframe.columns if column not in ordered_columns]
    return dataframe[ordered_columns + extra_columns]


def _load_csv(data_dir: Path, filename: str, expected_columns: list[str]) -> pd.DataFrame:
    path = _resolve_dataset_path(data_dir, filename)
    dataframe = pd.read_csv(path)
    return _normalise_columns(dataframe, expected_columns)


def _load_jsonl(data_dir: Path, filename: str, expected_columns: list[str]) -> pd.DataFrame:
    path = _resolve_dataset_path(data_dir, filename)
    dataframe = pd.read_json(path, lines=True)
    return _normalise_columns(dataframe, expected_columns)


def load_customers(data_dir: Path | str = DEFAULT_DATA_DIR) -> pd.DataFrame:
    return _load_csv(Path(data_dir), "customers.csv", CUSTOMER_FIELDS)


def load_accounts(data_dir: Path | str = DEFAULT_DATA_DIR) -> pd.DataFrame:
    return _load_csv(Path(data_dir), "accounts.csv", ACCOUNT_FIELDS)


def load_transactions(data_dir: Path | str = DEFAULT_DATA_DIR) -> pd.DataFrame:
    return _load_jsonl(Path(data_dir), "transactions.jsonl", TRANSACTION_FIELDS)


def load_device_sessions(data_dir: Path | str = DEFAULT_DATA_DIR) -> pd.DataFrame:
    return _load_jsonl(Path(data_dir), "device_sessions.jsonl", SESSION_FIELDS)


def load_fraud_labels(data_dir: Path | str = DEFAULT_DATA_DIR) -> pd.DataFrame:
    return _load_csv(Path(data_dir), "fraud_labels.csv", FRAUD_LABEL_FIELDS)


def load_aml_watchlist(data_dir: Path | str = DEFAULT_DATA_DIR) -> pd.DataFrame:
    return _load_csv(Path(data_dir), "aml_watchlist.csv", AML_WATCHLIST_FIELDS)


def load_all_datasets(data_dir: Path | str = DEFAULT_DATA_DIR) -> dict[str, pd.DataFrame]:
    raw_dir = Path(data_dir)
    return {
        "customers": load_customers(raw_dir),
        "accounts": load_accounts(raw_dir),
        "transactions": load_transactions(raw_dir),
        "device_sessions": load_device_sessions(raw_dir),
        "fraud_labels": load_fraud_labels(raw_dir),
        "aml_watchlist": load_aml_watchlist(raw_dir),
    }
