from copy import deepcopy
from pathlib import Path

import pytest
from src.reporting.build_powerbi_outputs import (
    PROHIBITED_COLUMNS,
    build_aggregate_tables,
    build_dimensions,
    build_fact_tables,
    generate_reporting_dictionary,
    load_reporting_config,
    load_reporting_sources,
    stable_surrogate_key,
    validate_reporting_model,
    validate_upstream_artefacts,
    write_powerbi_outputs,
)


@pytest.fixture(scope="module")
def reporting_model():
    config = load_reporting_config()
    sources = load_reporting_sources(config)
    dimensions = build_dimensions(sources, config)
    facts = build_fact_tables(sources, dimensions, config)
    aggregates = build_aggregate_tables(sources, facts, config)
    tables = {**dimensions, **facts, **aggregates}
    tables["reporting_data_dictionary"] = generate_reporting_dictionary(tables)
    return config, sources, dimensions, facts, aggregates, tables


def test_configuration_and_required_inputs_load() -> None:
    config = load_reporting_config()
    validate_upstream_artefacts(config)
    assert len(config["required_dimensions"]) == 7
    assert len(config["required_fact_tables"]) == 9


def test_surrogate_keys_are_deterministic() -> None:
    assert stable_surrogate_key("customer", "C1") == stable_surrogate_key("customer", "C1")
    assert stable_surrogate_key("customer", "C1") != stable_surrogate_key("customer", "C2")


def test_dimension_keys_and_fact_grains_are_unique(reporting_model) -> None:
    _, _, dimensions, facts, _, _ = reporting_model
    for table, key in [
        ("dim_customer", "customer_key"),
        ("dim_account", "account_key"),
        ("dim_date", "date_key"),
        ("dim_aml_rule", "aml_rule_key"),
    ]:
        assert dimensions[table][key].is_unique
    assert facts["fact_transactions"]["transaction_key"].is_unique
    assert facts["fact_aml_alerts"]["alert_key"].is_unique
    assert facts["fact_customer_risk"]["customer_key"].is_unique


def test_customer_account_transaction_rule_and_date_relationships_resolve(
    reporting_model,
) -> None:
    _, _, dimensions, facts, _, _ = reporting_model
    assert set(facts["fact_transactions"].customer_key) <= set(
        dimensions["dim_customer"].customer_key
    )
    assert set(facts["fact_transactions"].account_key) <= set(dimensions["dim_account"].account_key)
    assert set(facts["fact_transactions"].date_key) <= set(dimensions["dim_date"].date_key)
    assert set(facts["fact_aml_alerts"].aml_rule_key) <= set(
        dimensions["dim_aml_rule"].aml_rule_key
    )


def test_counts_and_kpis_reconcile(reporting_model) -> None:
    config, sources, _, facts, aggregates, tables = reporting_model
    quality = validate_reporting_model(tables, sources, config)
    assert quality["overall_status"] == "passed"
    assert len(facts["fact_transactions"]) == len(sources["transactions"])
    assert len(facts["fact_fraud_predictions"]) == len(sources["fraud_predictions"])
    assert len(facts["fact_aml_alerts"]) == len(sources["aml_alerts"])
    assert len(facts["fact_customer_risk"]) == len(sources["risk"])
    assert len(facts["fact_investigation_cases"]) == len(sources["cases"])
    assert len(facts["fact_monitoring_alerts"]) == len(sources["monitoring_alerts"])
    assert len(aggregates["agg_executive_kpis"]) == 21


def test_privacy_and_dictionary_coverage(reporting_model) -> None:
    _, _, _, _, _, tables = reporting_model
    all_columns = {column for frame in tables.values() for column in frame.columns}
    assert not (all_columns & PROHIBITED_COLUMNS)
    dictionary = tables["reporting_data_dictionary"]
    for name, frame in tables.items():
        if name == "reporting_data_dictionary":
            continue
        covered = set(dictionary.query("table_name == @name").column_name)
        assert set(frame.columns) <= covered


def test_semantic_and_dax_specs_reference_generated_tables(reporting_model) -> None:
    _, _, _, _, _, tables = reporting_model
    semantic = Path("dashboard/semantic_model_spec.md").read_text()
    dax = Path("dashboard/dax_measures.md").read_text()
    for table in [
        "dim_customer",
        "dim_account",
        "dim_date",
        "fact_transactions",
        "fact_aml_alerts",
    ]:
        assert table in semantic
    for table in [
        "fact_transactions",
        "fact_fraud_predictions",
        "fact_customer_risk",
        "fact_pipeline_health",
    ]:
        assert table in dax and table in tables


def test_missing_upstream_input_raises_clear_error(tmp_path: Path) -> None:
    config = deepcopy(load_reporting_config())
    config["customers_path"] = str(tmp_path / "missing.csv")
    with pytest.raises(FileNotFoundError, match="missing"):
        validate_upstream_artefacts(config)


def test_outputs_write_to_temporary_directory(tmp_path: Path, reporting_model) -> None:
    config, sources, _, _, _, tables = reporting_model
    config = deepcopy(config)
    config["output_directory"] = str(tmp_path / "powerbi")
    config["quality_summary_path"] = str(tmp_path / "quality.json")
    config["quality_report_path"] = str(tmp_path / "quality.md")
    quality = validate_reporting_model(tables, sources, config)
    paths = write_powerbi_outputs(tables, quality, config)
    assert all(path.exists() and path.stat().st_size > 0 for path in paths.values())
