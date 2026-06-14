from pathlib import Path
from random import Random

from src.data_generation.generate_banking_data import (
    ACCOUNT_FIELDS,
    AML_WATCHLIST_FIELDS,
    CUSTOMER_FIELDS,
    FRAUD_LABEL_FIELDS,
    generate_accounts,
    generate_all_datasets,
    generate_aml_watchlist,
    generate_customers,
    generate_device_sessions,
    generate_fraud_labels,
    generate_transactions,
    write_all_datasets,
    write_csv,
    write_jsonl,
)

TEST_CONFIG = {
    "random_seed": 7,
    "number_of_customers": 10,
    "accounts_per_customer_min": 1,
    "accounts_per_customer_max": 2,
    "transactions_per_account_min": 2,
    "transactions_per_account_max": 4,
    "output_dir": "data/raw",
    "fraud_rate": 0.2,
    "aml_watchlist_rate": 0.2,
}


def test_generator_functions_return_non_empty_datasets() -> None:
    rng = Random(7)
    customers = generate_customers(5, rng)
    accounts = generate_accounts(customers, 1, 2, rng)
    sessions = generate_device_sessions(customers, rng)
    transactions = generate_transactions(accounts, sessions, 2, 3, rng)
    fraud_labels = generate_fraud_labels(transactions, 0.2, rng)
    aml_watchlist = generate_aml_watchlist(customers, 0.2, rng)

    assert customers
    assert accounts
    assert sessions
    assert transactions
    assert fraud_labels
    assert aml_watchlist


def test_customer_id_links_customers_to_accounts() -> None:
    datasets = generate_all_datasets(TEST_CONFIG)
    customer_ids = {customer["customer_id"] for customer in datasets["customers"]}

    assert {account["customer_id"] for account in datasets["accounts"]} <= customer_ids


def test_account_id_links_accounts_to_transactions() -> None:
    datasets = generate_all_datasets(TEST_CONFIG)
    account_ids = {account["account_id"] for account in datasets["accounts"]}

    assert {transaction["account_id"] for transaction in datasets["transactions"]} <= account_ids


def test_fraud_labels_reference_valid_transaction_ids() -> None:
    datasets = generate_all_datasets(TEST_CONFIG)
    transaction_ids = {transaction["transaction_id"] for transaction in datasets["transactions"]}

    assert {label["transaction_id"] for label in datasets["fraud_labels"]} <= transaction_ids


def test_aml_watchlist_references_valid_customer_ids() -> None:
    datasets = generate_all_datasets(TEST_CONFIG)
    customer_ids = {customer["customer_id"] for customer in datasets["customers"]}

    assert {alert["customer_id"] for alert in datasets["aml_watchlist"]} <= customer_ids


def test_output_files_can_be_written_successfully(tmp_path: Path) -> None:
    datasets = generate_all_datasets(TEST_CONFIG)
    output_paths = write_all_datasets(tmp_path, datasets)

    expected_names = {
        "customers.csv",
        "accounts.csv",
        "transactions.jsonl",
        "device_sessions.jsonl",
        "fraud_labels.csv",
        "aml_watchlist.csv",
    }

    assert {path.name for path in output_paths.values()} == expected_names
    assert all(path.exists() and path.stat().st_size > 0 for path in output_paths.values())


def test_individual_writers_create_files(tmp_path: Path) -> None:
    datasets = generate_all_datasets(TEST_CONFIG)
    csv_path = tmp_path / "customers.csv"
    jsonl_path = tmp_path / "transactions.jsonl"

    write_csv(csv_path, datasets["customers"], CUSTOMER_FIELDS)
    write_jsonl(jsonl_path, datasets["transactions"])

    assert csv_path.exists()
    assert jsonl_path.exists()
    assert ACCOUNT_FIELDS
    assert AML_WATCHLIST_FIELDS
    assert FRAUD_LABEL_FIELDS
