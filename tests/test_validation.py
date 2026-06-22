from pathlib import Path

from src.data_generation.generate_banking_data import generate_all_datasets, write_all_datasets
from src.ingestion.load_banking_data import load_all_datasets
from src.validation.validate_banking_data import (
    validate_all_datasets,
    write_validation_outputs,
)

TEST_CONFIG = {
    "random_seed": 13,
    "number_of_customers": 10,
    "accounts_per_customer_min": 1,
    "accounts_per_customer_max": 2,
    "transactions_per_account_min": 2,
    "transactions_per_account_max": 4,
    "output_dir": "data/raw",
    "fraud_rate": 0.2,
    "aml_watchlist_rate": 0.2,
}


def _load_generated_data(tmp_path: Path):
    datasets = generate_all_datasets(TEST_CONFIG)
    write_all_datasets(tmp_path, datasets)
    return load_all_datasets(tmp_path)


def test_validation_passes_on_generated_synthetic_data(tmp_path: Path) -> None:
    datasets = _load_generated_data(tmp_path)
    report = validate_all_datasets(datasets)

    assert report["overall_status"] == "passed"
    assert not report["failed_checks"]


def test_validation_detects_broken_transaction_account_relationship(tmp_path: Path) -> None:
    datasets = _load_generated_data(tmp_path)
    datasets["transactions"].loc[0, "account_id"] = "ACC-MISSING"

    report = validate_all_datasets(datasets)

    assert report["overall_status"] == "failed"
    assert any(
        check["category"] == "relationship" and check["status"] == "failed"
        for check in report["failed_checks"]
    )


def test_validation_output_files_can_be_written(tmp_path: Path) -> None:
    datasets = _load_generated_data(tmp_path / "raw")
    report = validate_all_datasets(datasets)
    markdown_path = tmp_path / "reports" / "data_validation_report.md"
    json_path = tmp_path / "outputs" / "data_validation_results.json"

    write_validation_outputs(report, markdown_path, json_path)

    assert markdown_path.exists()
    assert json_path.exists()
    assert "Data Validation Report" in markdown_path.read_text(encoding="utf-8")
    assert '"overall_status": "passed"' in json_path.read_text(encoding="utf-8")
