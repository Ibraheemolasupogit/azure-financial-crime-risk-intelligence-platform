import json
from copy import deepcopy
from pathlib import Path

import pandas as pd
import pytest
from src.genai.investigation_assistant import (
    build_grounding_quality,
    build_structured_evidence_packets,
    create_prompt_payload,
    generate_deterministic_case_summary,
    generate_executive_brief,
    generate_investigator_review_note,
    generate_sar_style_draft,
    load_genai_config,
    resolve_generation_mode,
    select_customers_for_investigation,
    validate_evidence_packet,
    validate_generated_case,
    write_investigation_outputs,
)


def _config() -> dict:
    return deepcopy(load_genai_config())


def _fixtures():
    scores = pd.DataFrame(
        [
            {
                "customer_id": "CUST-001",
                "total_risk_score": 80.0,
                "risk_band": "critical",
                "review_priority": "urgent",
                "score_version": "1.0",
                "primary_risk_reason": "Multiple high-severity AML alerts",
                "secondary_risk_reason": "Elevated model probability",
                "total_aml_alerts": 25,
                "maximum_fraud_probability": 0.9,
                "predicted_fraud_transaction_count": 2,
            }
        ]
    )
    components = pd.DataFrame(
        [
            {
                "customer_id": "CUST-001",
                "component_name": name,
                "normalised_score": score,
                "weighted_contribution": score / 5,
            }
            for name, score in [
                ("kyc", 40),
                ("transaction_behaviour", 70),
                ("aml_alert", 90),
                ("fraud_model", 80),
                ("device_session", 60),
            ]
        ]
    )
    alerts = pd.DataFrame(
        [
            {
                "alert_id": "ALERT-001",
                "customer_id": "CUST-001",
                "rule_id": "AML001",
                "transaction_id": "TXN-001",
                "transaction_timestamp": "2025-01-01T00:00:00",
                "alert_severity": "high",
                "risk_points": 30,
                "reason": "Amount exceeded configured synthetic threshold.",
                "evidence_json": json.dumps({"transaction_amount": 600.0}),
            }
        ]
    )
    aml_summary = pd.DataFrame(
        [
            {
                "customer_id": "CUST-001",
                "total_aml_alerts": 25,
                "distinct_rules_triggered": 1,
                "total_aml_risk_points": 750,
            }
        ]
    )
    explanations = pd.DataFrame(
        [
            {
                "transaction_id": "TXN-001",
                "customer_id": "CUST-001",
                "transaction_timestamp": "2025-01-01T00:00:00",
                "fraud_probability": 0.9,
                "predicted_fraud_label": 1,
                "error_type": "false_positive",
                "explanation_status": "passed",
            }
        ]
    )
    reasons = pd.DataFrame(
        [
            {
                "transaction_id": "TXN-001",
                "reason_code": "FRC_AMOUNT_UP",
                "reason_direction": "positive",
                "source_feature_name": "amount",
                "observed_value": 600.0,
                "contribution": 1.2,
                "human_readable_reason": "Observed amount increased the model score.",
                "reason_rank": 1,
            }
        ]
    )
    return scores, components, alerts, aml_summary, explanations, reasons


def _packet(config=None):
    config = config or _config()
    scores, components, alerts, aml_summary, explanations, reasons = _fixtures()
    selected = select_customers_for_investigation(scores, config)
    return build_structured_evidence_packets(
        selected,
        components,
        alerts,
        aml_summary,
        explanations,
        reasons,
        {"overall_status": "passed"},
        config,
    )[0]


def test_default_configuration_is_local_and_safe() -> None:
    config = load_genai_config()
    assert config["generation_mode"] == "deterministic_template"
    assert config["include_personal_details"] is False


def test_selection_case_ids_and_packets_are_deterministic() -> None:
    first = _packet()
    second = _packet()
    assert first == second
    assert first["case_id"].startswith("CASE-")
    assert {
        "case_id",
        "component_scores",
        "top_aml_alerts",
        "human_review_required",
    } <= first.keys()


def test_packets_exclude_personal_details_and_are_valid_json() -> None:
    packet = _packet()
    validate_evidence_packet(packet)
    text = json.dumps(packet)
    assert "first_name" not in text and "date_of_birth" not in text


def test_summaries_and_sar_drafts_are_safe_grounded_drafts() -> None:
    config = _config()
    packet = _packet(config)
    summary = generate_deterministic_case_summary(packet, config)
    sar = generate_sar_style_draft(packet, config)
    validation = validate_generated_case(packet, summary, sar, config)
    assert validation["passed"]
    assert "human review" in summary["case_summary"].lower()
    assert sar["not_for_submission"] is True
    assert "not for submission" in sar["draft_narrative"].lower()


def test_prompt_payload_disables_network_and_placeholder_falls_back() -> None:
    config = _config()
    config["generation_mode"] = "azure_openai_placeholder"
    payload = create_prompt_payload(_packet(config), config)
    assert payload["provider"] == "azure_openai"
    assert payload["network_call_enabled"] is False
    assert resolve_generation_mode(config) == "deterministic_template"


def test_grounding_detects_invented_numbers_and_references() -> None:
    config = _config()
    packet = _packet(config)
    summary = generate_deterministic_case_summary(packet, config)
    sar = generate_sar_style_draft(packet, config)
    summary["case_summary"] += " Invented amount 999999 and TXN-FAKE under AML999."
    validation = validate_generated_case(packet, summary, sar, config)
    assert not validation["passed"]
    assert validation["unsupported_numeric_claims"]
    assert validation["unsupported_transaction_references"] == ["TXN-FAKE"]
    assert validation["unsupported_aml_rule_references"] == ["AML999"]


def test_prohibited_claims_and_word_limits_are_detected() -> None:
    config = _config()
    config["maximum_narrative_words"] = 5
    packet = _packet(config)
    summary = generate_deterministic_case_summary(packet, config)
    sar = generate_sar_style_draft(packet, config)
    summary["case_summary"] += " The customer committed fraud."
    validation = validate_generated_case(packet, summary, sar, config)
    assert validation["prohibited_claim_violations"]
    assert validation["word_limit_violations"]


def test_review_note_and_executive_brief_require_human_review() -> None:
    config = _config()
    packet = _packet(config)
    summary = generate_deterministic_case_summary(packet, config)
    note = generate_investigator_review_note(packet, summary, config)
    brief = generate_executive_brief([packet], pd.DataFrame([summary]), config)
    assert "human review" in note.lower()
    assert "human" in brief.lower() and "synthetic" in brief.lower()


def test_empty_case_selection_is_handled() -> None:
    scores, *_ = _fixtures()
    scores["total_risk_score"] = 1.0
    assert select_customers_for_investigation(scores, _config()).empty


def test_quality_aggregation_reports_failures() -> None:
    quality = build_grounding_quality(
        [
            {
                "passed": False,
                "unsupported_numeric_claims": ["9"],
                "unsupported_transaction_references": [],
                "unsupported_aml_rule_references": [],
                "prohibited_claim_violations": [],
                "disclaimer_violations": [],
                "word_limit_violations": [],
                "case_id": "C",
            }
        ],
        "deterministic_template",
    )
    assert quality["overall_status"] == "failed"


def test_outputs_are_reproducible_and_writable(tmp_path: Path) -> None:
    config = _config()
    for key in [
        "evidence_packets_path",
        "case_summaries_path",
        "sar_drafts_path",
        "executive_brief_path",
        "prompt_payloads_path",
        "grounding_quality_path",
    ]:
        config[key] = str(tmp_path / Path(config[key]).name)
    config["investigation_report_dir"] = str(tmp_path / "cases")
    packet = _packet(config)
    summary = generate_deterministic_case_summary(packet, config)
    sar = generate_sar_style_draft(packet, config)
    validation = validate_generated_case(packet, summary, sar, config)
    quality = build_grounding_quality([validation], "deterministic_template")
    paths = write_investigation_outputs(
        [packet],
        pd.DataFrame([summary]),
        pd.DataFrame([sar]),
        [create_prompt_payload(packet, config)],
        {packet["case_id"]: generate_investigator_review_note(packet, summary, config)},
        generate_executive_brief([packet], pd.DataFrame([summary]), config),
        quality,
        config,
    )
    assert all(path.exists() for path in paths.values())
    assert list((tmp_path / "cases").glob("*.md"))


def test_malformed_packet_raises_clear_error() -> None:
    with pytest.raises(ValueError, match="missing required fields"):
        validate_evidence_packet({"case_id": "CASE-X"})
