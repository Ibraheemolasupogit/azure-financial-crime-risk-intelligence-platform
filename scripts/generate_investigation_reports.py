#!/usr/bin/env python
"""Generate local, grounded, synthetic investigation drafts without model calls."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> int:
    from src.genai.investigation_assistant import (
        build_grounding_quality,
        build_structured_evidence_packets,
        create_prompt_payload,
        generate_deterministic_case_summary,
        generate_executive_brief,
        generate_investigator_review_note,
        generate_sar_style_draft,
        load_aml_alerts,
        load_aml_customer_summaries,
        load_customer_risk_components,
        load_customer_risk_scores,
        load_genai_config,
        load_model_explanations,
        resolve_generation_mode,
        select_customers_for_investigation,
        validate_generated_case,
        write_investigation_outputs,
    )

    try:
        config = load_genai_config()
        scores = load_customer_risk_scores(config["customer_risk_scores_path"])
        components = load_customer_risk_components(config["customer_risk_components_path"])
        aml_alerts = load_aml_alerts(config["aml_alerts_path"])
        aml_summaries = load_aml_customer_summaries(config["aml_customer_summary_path"])
        explanations = load_model_explanations(config["local_explanations_path"])
        reason_codes = pd.read_csv(config["reason_codes_path"])
        explanation_quality = json.loads(
            Path(config["explanation_quality_path"]).read_text(encoding="utf-8")
        )
        selected = select_customers_for_investigation(scores, config)
        packets = build_structured_evidence_packets(
            selected,
            components,
            aml_alerts,
            aml_summaries,
            explanations,
            reason_codes,
            explanation_quality,
            config,
        )
        mode = resolve_generation_mode(config)
        summary_rows = []
        sar_rows = []
        prompts = []
        notes = {}
        validations = []
        for packet in packets:
            summary = generate_deterministic_case_summary(packet, config)
            sar = generate_sar_style_draft(packet, config)
            validation = validate_generated_case(packet, summary, sar, config)
            status = "passed" if validation["passed"] else "failed"
            summary["grounding_status"] = status
            summary["safety_status"] = status
            sar["grounding_status"] = status
            sar["safety_status"] = status
            summary_rows.append(summary)
            sar_rows.append(sar)
            prompts.append(create_prompt_payload(packet, config))
            notes[packet["case_id"]] = generate_investigator_review_note(
                packet, summary, config
            )
            validations.append(validation)
        summaries = pd.DataFrame(summary_rows)
        sar_drafts = pd.DataFrame(sar_rows)
        quality = build_grounding_quality(validations, mode)
        executive_brief = generate_executive_brief(packets, summaries, config)
        paths = write_investigation_outputs(
            packets,
            summaries,
            sar_drafts,
            prompts,
            notes,
            executive_brief,
            quality,
            config,
        )
    except (FileNotFoundError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        print(f"Investigation report generation failed: {error}")
        return 1

    print("Synthetic investigation report generation complete.")
    print(f"Generation mode: {mode}")
    print(f"Cases selected: {len(packets)}")
    print(f"Risk bands: {selected['risk_band'].value_counts().to_dict()}")
    print(f"Priorities represented: {selected['review_priority'].value_counts().to_dict()}")
    print(f"Evidence packets written: {len(packets)}")
    print(f"Case summaries generated: {len(summaries)}")
    print(f"Investigator reports generated: {len(notes)}")
    print(f"SAR-style drafts generated: {len(sar_drafts)}")
    print(
        f"Grounding pass/fail: {quality['grounding_checks_passed']}/"
        f"{quality['grounding_checks_failed']}"
    )
    print(
        f"Safety pass/fail: {quality['safety_checks_passed']}/"
        f"{quality['safety_checks_failed']}"
    )
    print(f"Evidence packets: {paths['packets']}")
    print(f"Prompt payloads: {paths['prompts']} (network disabled)")
    print(f"Case reports: {config['investigation_report_dir']}")
    print(f"Executive brief: {paths['executive_brief']}")
    return 0 if quality["overall_status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
