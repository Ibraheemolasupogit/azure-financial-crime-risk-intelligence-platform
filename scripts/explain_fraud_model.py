#!/usr/bin/env python
"""Generate native explanations for the persisted fraud baseline model."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> int:
    from src.explainability.explain_fraud_model import (
        aggregate_global_source_importance,
        build_error_type_analysis,
        build_explainability_summary,
        calculate_global_feature_importance,
        calculate_local_explanations,
        extract_logistic_coefficients,
        identify_transformed_features,
        load_explainability_config,
        load_final_model_feature_list,
        load_fraud_model_pipeline,
        load_fraud_test_predictions,
        load_transaction_feature_data,
        select_investigator_samples,
        write_explainability_outputs,
        write_explainability_report,
        write_investigator_packets,
    )

    try:
        config = load_explainability_config()
        pipeline = load_fraud_model_pipeline(config["model_path"])
        metadata = json.loads(Path(config["model_metadata_path"]).read_text(encoding="utf-8"))
        feature_list = load_final_model_feature_list(config["feature_list_path"])
        transaction_features = load_transaction_feature_data(
            config["transaction_features_path"]
        )
        predictions = load_fraud_test_predictions(config["predictions_path"])
        feature_dictionary = pd.read_csv(config["feature_dictionary_path"])

        mapping = identify_transformed_features(
            pipeline, feature_list, feature_dictionary
        )
        coefficients = extract_logistic_coefficients(pipeline, mapping)
        global_importance = calculate_global_feature_importance(coefficients)
        source_importance = aggregate_global_source_importance(global_importance)
        local, contributions, reasons, quality = calculate_local_explanations(
            pipeline,
            transaction_features,
            predictions,
            feature_list,
            mapping,
            config,
        )
        error_analysis = build_error_type_analysis(local, contributions, reasons)
        summary = build_explainability_summary(
            metadata,
            global_importance,
            source_importance,
            local,
            reasons,
            quality,
            error_analysis,
            len(predictions),
            int(config["top_global_feature_count"]),
        )
        output_paths = write_explainability_outputs(
            global_importance,
            source_importance,
            local,
            contributions,
            reasons,
            quality,
            error_analysis,
            summary,
            config,
        )
        samples = select_investigator_samples(
            local, int(config["explanation_sample_size"])
        )
        packet_paths = write_investigator_packets(
            samples,
            Path(config["investigator_packet_dir"]),
            str(summary["model_identifier"]),
        )
        report_path = Path(config["report_output_path"])
        write_explainability_report(summary, report_path)
    except (FileNotFoundError, KeyError, TypeError, ValueError) as error:
        print(f"Fraud model explainability failed: {error}")
        return 1

    print("Synthetic fraud model explainability complete.")
    print(f"Model type: {summary['model_type']}")
    print(f"Transactions explained: {summary['transactions_explained']}")
    print(f"Transformed features: {summary['transformed_features']}")
    print(f"Source features: {summary['source_features']}")
    print(
        f"Explanations passed/failed: {quality['explanations_passed']}/"
        f"{quality['explanations_failed']}"
    )
    print(
        "Maximum reconstruction differences: "
        f"decision={quality['maximum_decision_score_difference']:.3e}, "
        f"probability={quality['maximum_probability_difference']:.3e}"
    )
    strongest = global_importance.head(3)["transformed_feature_name"].tolist()
    print(f"Most influential transformed features: {', '.join(strongest)}")
    common = list(summary["common_local_reason_codes"].keys())[:3]
    print(f"Most common reason codes: {', '.join(common)}")
    print(f"Local explanations: {output_paths['local']}")
    print(f"Detailed contributions: {output_paths['contributions']}")
    print(f"Reason codes: {output_paths['reasons']}")
    print(f"Quality report: {output_paths['quality']}")
    print(f"Investigator packets: {len(packet_paths)} in {config['investigator_packet_dir']}")
    print(f"Explainability report: {report_path}")
    return 0 if quality["overall_status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
