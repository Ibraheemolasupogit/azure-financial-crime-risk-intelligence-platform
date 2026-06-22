#!/usr/bin/env python
"""Build governed Power BI-ready analytical tables locally."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> int:
    from src.reporting.build_powerbi_outputs import (
        build_aggregate_tables,
        build_dimensions,
        build_fact_tables,
        generate_reporting_dictionary,
        load_reporting_config,
        load_reporting_sources,
        validate_reporting_model,
        write_powerbi_outputs,
    )

    try:
        config = load_reporting_config()
        sources = load_reporting_sources(config)
        dimensions = build_dimensions(sources, config)
        facts = build_fact_tables(sources, dimensions, config)
        aggregates = build_aggregate_tables(sources, facts, config)
        tables = {**dimensions, **facts, **aggregates}
        dictionary = generate_reporting_dictionary(tables)
        tables["reporting_data_dictionary"] = dictionary
        quality = validate_reporting_model(tables, sources, config)
        paths = write_powerbi_outputs(tables, quality, config)
    except (FileNotFoundError, KeyError, TypeError, ValueError) as error:
        print(f"Power BI reporting build failed: {error}")
        return 1

    print("Power BI-ready analytical outputs complete.")
    print(f"Dimensions generated: {len(dimensions)}")
    print(f"Fact tables generated: {len(facts)}")
    print(f"Aggregate tables generated: {len(aggregates)}")
    for name in sorted(tables):
        print(f"- {name}: {len(tables[name])} rows")
    relationship = quality["relationship_checks"]
    reconciliation = quality["reconciliation_checks"]
    print(
        "Relationship checks passed/failed: "
        f"{sum(item['status'] == 'passed' for item in relationship)}/"
        f"{sum(item['status'] == 'failed' for item in relationship)}"
    )
    print(
        "Reconciliation checks passed/failed: "
        f"{sum(item['status'] == 'passed' for item in reconciliation)}/"
        f"{sum(item['status'] == 'failed' for item in reconciliation)}"
    )
    print(f"Privacy checks: {quality['privacy_checks']}")
    print(f"KPI count: {len(aggregates['agg_executive_kpis'])}")
    print(f"Reporting quality status: {quality['overall_status']}")
    print(f"Output directory: {config['output_directory']}")
    print(f"Quality report: {paths['report']}")
    return 0 if quality["overall_status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
