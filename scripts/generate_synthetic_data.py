#!/usr/bin/env python
"""CLI for generating local synthetic banking datasets."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


CONFIG_PATH = Path("configs/data_generation_config.yaml")


def load_config(config_path: Path = CONFIG_PATH) -> dict:
    with config_path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def main() -> None:
    from src.data_generation.generate_banking_data import generate_all_datasets, write_all_datasets

    config = load_config()
    datasets = generate_all_datasets(config)
    output_dir = Path(config["output_dir"])
    write_all_datasets(output_dir, datasets)

    print("Synthetic banking data generation complete.")
    print(f"Output directory: {output_dir}")
    for dataset_name, rows in datasets.items():
        print(f"- {dataset_name}: {len(rows)} rows")


if __name__ == "__main__":
    main()
