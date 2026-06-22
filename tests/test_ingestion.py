from pathlib import Path

import pytest
from src.data_generation.generate_banking_data import (
    ACCOUNT_FIELDS,
    AML_WATCHLIST_FIELDS,
    CUSTOMER_FIELDS,
    FRAUD_LABEL_FIELDS,
    SESSION_FIELDS,
    TRANSACTION_FIELDS,
    generate_all_datasets,
    write_all_datasets,
)
from src.ingestion.load_banking_data import load_all_datasets, load_customers

TEST_CONFIG = {
    "random_seed": 11,
    "number_of_customers": 8,
    "accounts_per_customer_min": 1,
    "accounts_per_customer_max": 2,
    "transactions_per_account_min": 2,
    "transactions_per_account_max": 3,
    "output_dir": "data/raw",
    "fraud_rate": 0.2,
    "aml_watchlist_rate": 0.2,
}

EXPECTED_COLUMNS = {
    "customers": CUSTOMER_FIELDS,
    "accounts": ACCOUNT_FIELDS,
    "transactions": TRANSACTION_FIELDS,
    "device_sessions": SESSION_FIELDS,
    "fraud_labels": FRAUD_LABEL_FIELDS,
    "aml_watchlist": AML_WATCHLIST_FIELDS,
}


def _write_test_data(output_dir: Path) -> None:
    datasets = generate_all_datasets(TEST_CONFIG)
    write_all_datasets(output_dir, datasets)


def test_all_datasets_can_be_loaded_from_generated_test_data(tmp_path: Path) -> None:
    _write_test_data(tmp_path)
    loaded = load_all_datasets(tmp_path)

    assert set(loaded) == set(EXPECTED_COLUMNS)
    assert all(not dataframe.empty for dataframe in loaded.values())


def test_loaded_datasets_include_expected_columns(tmp_path: Path) -> None:
    _write_test_data(tmp_path)
    loaded = load_all_datasets(tmp_path)

    for dataset_name, expected_columns in EXPECTED_COLUMNS.items():
        assert list(loaded[dataset_name].columns[: len(expected_columns)]) == expected_columns


def test_missing_file_error_is_clear(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Required dataset file not found"):
        load_customers(tmp_path)
