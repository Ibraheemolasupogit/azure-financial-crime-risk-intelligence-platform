"""Safe deterministic investigation drafts grounded in synthetic structured evidence."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from src.genai.prompt_templates import (
    CASE_SUMMARY_TEMPLATE,
    SYSTEM_CONSTRAINTS,
    expected_case_output_schema,
)

PERSONAL_DETAIL_FIELDS = {"first_name", "last_name", "date_of_birth", "address", "email", "phone"}


def load_genai_config(
    path: Path | str = "configs/genai_investigation_config.yaml",
) -> dict[str, Any]:
    """Load and validate safe investigation-generation settings."""
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"GenAI investigation configuration not found: {config_path}")
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ValueError("GenAI investigation configuration must be a mapping.")
    if config["generation_mode"] not in {"deterministic_template", "azure_openai_placeholder"}:
        raise ValueError("Unsupported generation_mode; no network-capable mode is available.")
    if config["include_personal_details"]:
        raise ValueError("include_personal_details must remain false for this milestone.")
    if int(config["maximum_cases"]) < 0:
        raise ValueError("maximum_cases cannot be negative.")
    return config


def _load_csv(path: str, label: str) -> pd.DataFrame:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Required {label} file not found: {file_path}")
    return pd.read_csv(file_path)


def load_customer_risk_scores(path: str) -> pd.DataFrame:
    data = _load_csv(path, "customer risk scores")
    required = {"customer_id", "total_risk_score", "risk_band", "review_priority"}
    _require(data, required, "risk scores")
    return data


def load_customer_risk_components(path: str) -> pd.DataFrame:
    data = _load_csv(path, "customer risk components")
    _require(data, {"customer_id", "component_name", "normalised_score"}, "risk components")
    return data


def load_aml_alerts(path: str) -> pd.DataFrame:
    data = _load_csv(path, "AML alerts")
    _require(data, {"customer_id", "rule_id", "transaction_id", "risk_points"}, "AML alerts")
    return data


def load_aml_customer_summaries(path: str) -> pd.DataFrame:
    data = _load_csv(path, "AML customer summaries")
    _require(data, {"customer_id", "total_aml_alerts", "distinct_rules_triggered"}, "AML summaries")
    return data


def load_fraud_predictions(path: str) -> pd.DataFrame:
    data = _load_csv(path, "fraud predictions")
    _require(data, {"transaction_id", "fraud_probability", "error_type"}, "fraud predictions")
    return data


def load_model_explanations(path: str) -> pd.DataFrame:
    data = _load_csv(path, "model explanations")
    _require(data, {"transaction_id", "customer_id", "explanation_status"}, "model explanations")
    return data


def _require(data: pd.DataFrame, columns: set[str], label: str) -> None:
    missing = sorted(columns - set(data.columns))
    if missing:
        raise ValueError(f"{label} is missing required columns: {missing}")


def select_customers_for_investigation(
    scores: pd.DataFrame, config: dict[str, Any]
) -> pd.DataFrame:
    """Select a limited deterministic set of high-priority synthetic customers."""
    eligible = scores[
        scores["risk_band"].isin(config["included_risk_bands"])
        & scores["review_priority"].isin(config["included_review_priorities"])
        & scores["total_risk_score"].ge(float(config["minimum_total_risk_score"]))
        & (
            scores["total_aml_alerts"].ge(int(config["minimum_aml_alert_count"]))
            | scores["maximum_fraud_probability"].ge(
                float(config["minimum_fraud_probability"])
            )
        )
    ].copy()
    return eligible.sort_values(
        ["total_risk_score", "total_aml_alerts", "customer_id"],
        ascending=[False, False, True],
        kind="stable",
    ).head(int(config["maximum_cases"]))


def _case_id(customer_id: str, config: dict[str, Any]) -> str:
    source = f"{customer_id}|{config['output_version']}|{config['deterministic_timestamp']}"
    return f"CASE-{hashlib.sha256(source.encode()).hexdigest()[:12].upper()}"


def build_structured_evidence_packets(
    selected: pd.DataFrame,
    components: pd.DataFrame,
    aml_alerts: pd.DataFrame,
    aml_summaries: pd.DataFrame,
    explanations: pd.DataFrame,
    reason_codes: pd.DataFrame,
    explanation_quality: dict[str, Any],
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    """Build minimised, validated evidence packets for selected customers."""
    packets = []
    aml_lookup = aml_summaries.set_index("customer_id")
    for score in selected.itertuples():
        customer_id = str(score.customer_id)
        customer_components = components[components["customer_id"].eq(customer_id)].sort_values(
            ["weighted_contribution", "component_name"], ascending=[False, True]
        )
        customer_alerts = aml_alerts[aml_alerts["customer_id"].eq(customer_id)].sort_values(
            ["risk_points", "transaction_timestamp", "alert_id"],
            ascending=[False, False, True],
        )
        customer_explanations = explanations[
            explanations["customer_id"].eq(customer_id)
        ].sort_values(["fraud_probability", "transaction_id"], ascending=[False, True])
        top_explanations = customer_explanations.head(
            int(config["top_fraud_transaction_count"])
        )
        transaction_ids = top_explanations["transaction_id"].tolist()
        selected_reasons = reason_codes[
            reason_codes["transaction_id"].isin(transaction_ids)
        ].sort_values(["transaction_id", "reason_rank", "reason_direction"])
        aml_summary = (
            aml_lookup.loc[customer_id].to_dict() if customer_id in aml_lookup.index else {}
        )
        top_alerts = []
        for alert in customer_alerts.head(int(config["top_aml_alert_count"])).itertuples():
            top_alerts.append(
                {
                    "alert_id": alert.alert_id,
                    "rule_id": alert.rule_id,
                    "transaction_id": alert.transaction_id,
                    "transaction_timestamp": alert.transaction_timestamp,
                    "severity": alert.alert_severity,
                    "risk_points": int(alert.risk_points),
                    "reason": alert.reason,
                    "evidence": json.loads(alert.evidence_json),
                }
            )
        fraud_details = top_explanations[
            [
                "transaction_id",
                "transaction_timestamp",
                "fraud_probability",
                "predicted_fraud_label",
                "error_type",
                "explanation_status",
            ]
        ].to_dict(orient="records")
        packet = {
            "case_id": _case_id(customer_id, config),
            "customer_id": customer_id if config["include_customer_identifiers"] else "redacted",
            "total_risk_score": float(score.total_risk_score),
            "risk_band": score.risk_band,
            "review_priority": score.review_priority,
            "score_version": score.score_version,
            "primary_risk_reason": score.primary_risk_reason,
            "secondary_risk_reason": score.secondary_risk_reason,
            "component_scores": {
                row.component_name: float(row.normalised_score)
                for row in customer_components.itertuples()
            },
            "aml_alert_summary": {
                "total_aml_alerts": int(aml_summary.get("total_aml_alerts", 0)),
                "distinct_aml_rules": int(aml_summary.get("distinct_rules_triggered", 0)),
                "total_aml_risk_points": int(aml_summary.get("total_aml_risk_points", 0)),
            },
            "top_aml_alerts": top_alerts,
            "triggered_aml_rule_identifiers": sorted(customer_alerts["rule_id"].unique()),
            "total_aml_risk_points": int(aml_summary.get("total_aml_risk_points", 0)),
            "fraud_prediction_summary": {
                "maximum_fraud_probability": float(score.maximum_fraud_probability),
                "predicted_fraud_transaction_count": int(
                    score.predicted_fraud_transaction_count
                ),
            },
            "highest_fraud_probabilities": fraud_details,
            "selected_fraud_model_reason_codes": selected_reasons.head(
                int(config["top_model_reason_count"])
            )[
                [
                    "transaction_id",
                    "reason_code",
                    "reason_direction",
                    "source_feature_name",
                    "observed_value",
                    "contribution",
                    "human_readable_reason",
                ]
            ].to_dict(orient="records"),
            "model_explanation_quality_status": explanation_quality["overall_status"],
            "relevant_transaction_identifiers": sorted(
                set(customer_alerts["transaction_id"]) | set(transaction_ids)
            )
            if config["include_transaction_identifiers"]
            else [],
            "relevant_transaction_timestamps": sorted(
                set(customer_alerts["transaction_timestamp"].astype(str))
                | set(top_explanations["transaction_timestamp"].astype(str))
            ),
            "evidence_source_references": [
                config["customer_risk_scores_path"],
                config["customer_risk_components_path"],
                config["aml_alerts_path"],
                config["local_explanations_path"],
                config["reason_codes_path"],
            ],
            "generated_timestamp": config["deterministic_timestamp"],
            "synthetic_data_flag": True,
            "human_review_required": True,
        }
        validate_evidence_packet(packet)
        packets.append(packet)
    return packets


def validate_evidence_packet(packet: dict[str, Any]) -> None:
    """Validate required fields and data minimisation."""
    required = {
        "case_id",
        "customer_id",
        "total_risk_score",
        "risk_band",
        "review_priority",
        "component_scores",
        "top_aml_alerts",
        "highest_fraud_probabilities",
        "synthetic_data_flag",
        "human_review_required",
    }
    missing = sorted(required - set(packet))
    if missing:
        raise ValueError(f"Evidence packet is missing required fields: {missing}")
    prohibited = PERSONAL_DETAIL_FIELDS & set(packet)
    if prohibited:
        raise ValueError(
            f"Evidence packet contains prohibited personal details: {sorted(prohibited)}"
        )
    json.dumps(packet, sort_keys=True, default=str)


def _disclaimers(config: dict[str, Any]) -> str:
    return " ".join(config["required_disclaimers"])


def generate_deterministic_case_summary(
    packet: dict[str, Any], config: dict[str, Any]
) -> dict[str, Any]:
    """Generate a neutral case summary from packet facts only."""
    aml = packet["aml_alert_summary"]
    fraud = packet["fraud_prediction_summary"]
    rules = ", ".join(packet["triggered_aml_rule_identifiers"]) or "none"
    summary = (
        f"Observed facts: synthetic customer {packet['customer_id']} has {aml['total_aml_alerts']} "
        f"AML alerts across {aml['distinct_aml_rules']} rules ({rules}); the maximum available "
        "fraud "
        f"probability is {fraud['maximum_fraud_probability']:.4f}. Analytical indicators: the "
        f"configured customer risk score is {packet['total_risk_score']:.4f} in the "
        f"{packet['risk_band']} band with {packet['review_priority']} review priority. "
        "Recommended review actions: a human investigator should verify transaction context, "
        "review KYC and device history, examine related alerts, and document a disposition. "
        f"{_disclaimers(config)}"
    )
    next_steps = (
        "Human review: verify source and destination context; review transaction history, KYC, "
        "device and authentication evidence; examine related alerts; document disposition."
    )
    return {
        "case_id": packet["case_id"],
        "customer_id": packet["customer_id"],
        "total_risk_score": packet["total_risk_score"],
        "risk_band": packet["risk_band"],
        "review_priority": packet["review_priority"],
        "case_summary": summary,
        "primary_risk_driver": packet["primary_risk_reason"],
        "secondary_risk_driver": packet["secondary_risk_reason"],
        "aml_alert_count": aml["total_aml_alerts"],
        "distinct_aml_rules": aml["distinct_aml_rules"],
        "maximum_fraud_probability": fraud["maximum_fraud_probability"],
        "model_explanation_status": packet["model_explanation_quality_status"],
        "recommended_next_steps": next_steps,
        "generation_mode": "deterministic_template",
        "grounding_status": "pending",
        "safety_status": "pending",
        "human_review_required": True,
        "synthetic_data_flag": True,
        "output_version": config["output_version"],
    }


def generate_sar_style_draft(packet: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    """Generate a controlled training-only SAR-style narrative."""
    alerts = packet["top_aml_alerts"]
    identifiers = [item["transaction_id"] for item in alerts]
    rules = packet["triggered_aml_rule_identifiers"]
    observed = (
        f"Structured synthetic evidence records {packet['aml_alert_summary']['total_aml_alerts']} "
        f"AML alerts and transaction references {', '.join(identifiers) or 'none available'}."
    )
    indicators = f"Configured rules referenced: {', '.join(rules) or 'none'}."
    uncertainties = (
        "The evidence does not establish intent or wrongdoing; legitimate explanations and data "
        "quality require investigator assessment."
    )
    narrative = (
        f"Training portfolio artefact, not an official report and not for submission. {observed} "
        f"{indicators} {uncertainties} Investigator validation is required. {_disclaimers(config)}"
    )
    return {
        "case_id": packet["case_id"],
        "customer_id": packet["customer_id"],
        "narrative_title": f"Training-only structured activity draft for {packet['case_id']}",
        "draft_narrative": narrative,
        "observed_activity_summary": observed,
        "supporting_indicators": indicators,
        "uncertainties": uncertainties,
        "human_review_required": True,
        "not_for_submission": True,
        "synthetic_data_flag": True,
        "generation_mode": "deterministic_template",
        "grounding_status": "pending",
        "safety_status": "pending",
    }


def create_prompt_payload(packet: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    """Create a disabled future Azure OpenAI payload without making a network call."""
    return {
        "case_id": packet["case_id"],
        "system_instruction": SYSTEM_CONSTRAINTS,
        "user_prompt": CASE_SUMMARY_TEMPLATE.format(
            evidence_json=json.dumps(packet, sort_keys=True, default=str)
        ),
        "structured_evidence": packet,
        "prohibited_behaviours": config["prohibited_claims"],
        "required_disclaimers": config["required_disclaimers"],
        "expected_output_schema": expected_case_output_schema(),
        "provider": "azure_openai",
        "deployment_placeholder": "disabled-milestone-9-deployment",
        "network_call_enabled": False,
        "synthetic_data_flag": True,
    }


def resolve_generation_mode(config: dict[str, Any]) -> str:
    """Safely fall back from placeholder cloud mode without any network activity."""
    return "deterministic_template"


def _packet_numbers(packet: dict[str, Any]) -> set[str]:
    values: set[str] = set()

    def collect(item: Any) -> None:
        if isinstance(item, dict):
            for value in item.values():
                collect(value)
        elif isinstance(item, list):
            for value in item:
                collect(value)
        elif isinstance(item, (int, float)) and not isinstance(item, bool):
            values.add(str(item))
            values.add(f"{float(item):.4f}")

    collect(packet)
    return values


def validate_generated_case(
    packet: dict[str, Any], summary: dict[str, Any], sar: dict[str, Any], config: dict[str, Any]
) -> dict[str, Any]:
    """Conservatively validate grounding, safety, references, and disclaimers."""
    texts = " ".join(
        [summary["case_summary"], summary["recommended_next_steps"], sar["draft_narrative"]]
    )
    allowed_transactions = set(packet["relevant_transaction_identifiers"])
    mentioned_transactions = set(re.findall(r"TXN-[A-Z0-9-]+", texts))
    allowed_rules = set(packet["triggered_aml_rule_identifiers"])
    mentioned_rules = set(re.findall(r"AML\d{3}", texts))
    numbers = set(re.findall(r"(?<![\w-])\d+(?:\.\d+)?(?![\w-])", texts))
    unsupported_numbers = sorted(numbers - _packet_numbers(packet))
    prohibited = [claim for claim in config["prohibited_claims"] if claim.lower() in texts.lower()]
    disclaimer_violations = [
        item for item in config["required_disclaimers"] if item not in texts
    ]
    if config["require_human_review_statement"] and "human review" not in texts.lower():
        disclaimer_violations.append("human review statement")
    if config["require_synthetic_data_statement"] and "synthetic" not in texts.lower():
        disclaimer_violations.append("synthetic data statement")
    word_violations = []
    if len(summary["case_summary"].split()) > int(config["maximum_narrative_words"]):
        word_violations.append("case_summary")
    if len(sar["draft_narrative"].split()) > int(config["maximum_narrative_words"]):
        word_violations.append("sar_style_draft")
    unsupported_transactions = sorted(mentioned_transactions - allowed_transactions)
    unsupported_rules = sorted(mentioned_rules - allowed_rules)
    passed = not any(
        [
            unsupported_numbers,
            unsupported_transactions,
            unsupported_rules,
            prohibited,
            disclaimer_violations,
            word_violations,
        ]
    )
    return {
        "case_id": packet["case_id"],
        "passed": passed,
        "unsupported_numeric_claims": unsupported_numbers,
        "unsupported_transaction_references": unsupported_transactions,
        "unsupported_aml_rule_references": unsupported_rules,
        "prohibited_claim_violations": prohibited,
        "disclaimer_violations": disclaimer_violations,
        "word_limit_violations": word_violations,
    }


def build_grounding_quality(
    validations: list[dict[str, Any]], mode: str
) -> dict[str, Any]:
    """Aggregate grounding and safety validation outcomes."""
    failures = [item for item in validations if not item["passed"]]
    def flatten(key: str) -> list[Any]:
        return [value for item in validations for value in item[key]]
    return {
        "run_timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
        "generation_mode": mode,
        "cases_generated": len(validations),
        "grounding_checks_passed": len(validations) - len(failures),
        "grounding_checks_failed": len(failures),
        "safety_checks_passed": len(validations) - len(failures),
        "safety_checks_failed": len(failures),
        "unsupported_numeric_claims": flatten("unsupported_numeric_claims"),
        "unsupported_transaction_references": flatten("unsupported_transaction_references"),
        "unsupported_aml_rule_references": flatten("unsupported_aml_rule_references"),
        "prohibited_claim_violations": flatten("prohibited_claim_violations"),
        "disclaimer_violations": flatten("disclaimer_violations"),
        "word_limit_violations": flatten("word_limit_violations"),
        "deterministic_output_status": "passed",
        "overall_status": "passed" if not failures else "failed",
        "synthetic_data_statement": "All generated cases and evidence are synthetic.",
    }


def generate_investigator_review_note(
    packet: dict[str, Any], summary: dict[str, Any], config: dict[str, Any]
) -> str:
    """Generate a structured Markdown investigator note."""
    alerts = packet["top_aml_alerts"]
    fraud = packet["highest_fraud_probabilities"]
    reasons = packet["selected_fraud_model_reason_codes"]
    lines = [
        f"# Investigation Case {packet['case_id']}",
        "",
        f"- Synthetic customer: `{packet['customer_id']}`",
        f"- Review priority: `{packet['review_priority']}`",
        f"- Risk score and band: {packet['total_risk_score']:.4f} ({packet['risk_band']})",
        f"- Generation mode: `{resolve_generation_mode(config)}`",
        f"- Generated timestamp: `{packet['generated_timestamp']}`",
        "",
        "## Case Overview",
        "",
        summary["case_summary"],
        "",
        "## Observed Transaction Indicators",
        "",
    ]
    lines.extend(
        f"- `{item['transaction_id']}` at `{item['transaction_timestamp']}`: {item['reason']}"
        for item in alerts
    )
    lines.extend(["", "## AML Rules Triggered", ""])
    lines.append(", ".join(f"`{rule}`" for rule in packet["triggered_aml_rule_identifiers"]))
    lines.extend(["", "## Fraud Model Indicators", ""])
    lines.extend(
        f"- `{item['transaction_id']}` probability {item['fraud_probability']:.4f}; "
        f"explanation `{item['explanation_status']}`"
        for item in fraud
    )
    lines.extend(["", "## Model Explanation Factors", ""])
    lines.extend(f"- {item['human_readable_reason']}" for item in reasons)
    lines.extend(
        [
            "",
            "## Evidence Table",
            "",
            "| Evidence | Value |",
            "| --- | --- |",
            f"| AML alerts | {packet['aml_alert_summary']['total_aml_alerts']} |",
            f"| Distinct AML rules | {packet['aml_alert_summary']['distinct_aml_rules']} |",
            "| Maximum fraud probability | "
            f"{packet['fraud_prediction_summary']['maximum_fraud_probability']:.4f} |",
            "",
            "## Key Uncertainties And Possible Benign Explanations",
            "",
            "- Structured indicators do not establish intent or wrongdoing.",
            "- Travel, legitimate international activity, new devices, or expected customer "
            "behaviour may explain signals.",
            "- Data quality, model error, and broad rule thresholds may contribute false "
            "positives.",
            "",
            "## Recommended Investigator Checks",
            "",
            "- Verify source and destination context.",
            "- Review customer transaction history and KYC status.",
            "- Review device and authentication history.",
            "- Examine related alerts and document investigator disposition.",
            "",
            "## Limitations",
            "",
            "This is a deterministic analytical draft based only on supplied structured evidence.",
            "",
            _disclaimers(config),
        ]
    )
    return "\n".join(lines) + "\n"


def generate_executive_brief(
    packets: list[dict[str, Any]], summaries: pd.DataFrame, config: dict[str, Any]
) -> str:
    """Generate a concise deterministic portfolio briefing."""
    bands = Counter(packet["risk_band"] for packet in packets)
    priorities = Counter(packet["review_priority"] for packet in packets)
    rules = Counter(rule for packet in packets for rule in packet["triggered_aml_rule_identifiers"])
    components = Counter(
        max(packet["component_scores"], key=packet["component_scores"].get)
        for packet in packets
    ) if packets else Counter()
    high_ids = [packet["customer_id"] for packet in packets]
    lines = [
        "# Executive Synthetic Investigation Briefing",
        "",
        f"- Cases selected: {len(packets)}",
        f"- Risk bands: {dict(bands)}",
        f"- Review priorities: {dict(priorities)}",
        f"- High-priority synthetic identifiers: {', '.join(high_ids) or 'none'}",
        f"- Dominant AML rules: {rules.most_common(5)}",
        f"- Dominant risk components: {components.most_common(5)}",
        "",
        "## Operational View",
        "",
        "The selected cases combine elevated configured customer-risk scores, AML alert exposure, "
        "and fraud-model indicators. The fraud baseline has weak synthetic discrimination and a "
        "substantial false-positive burden, so model scores require careful contextual review.",
        "",
        "Key operational risks include broad AML thresholds, correlated indicators, duplicate "
        "investigation workload, data-quality dependency, and overreliance on generated drafts.",
        "",
        "Recommended controls: review scenario thresholds and score weights, assess false-positive "
        "capacity, verify evidence lineage, and require documented human disposition.",
        "",
        _disclaimers(config),
    ]
    brief = "\n".join(lines) + "\n"
    if len(brief.split()) > int(config["maximum_executive_brief_words"]):
        raise ValueError("Executive briefing exceeds configured word limit.")
    return brief


def write_investigation_outputs(
    packets: list[dict[str, Any]],
    summaries: pd.DataFrame,
    sar_drafts: pd.DataFrame,
    prompts: list[dict[str, Any]],
    notes: dict[str, str],
    executive_brief: str,
    quality: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Path]:
    """Write all deterministic investigation artifacts."""
    paths = {
        "packets": Path(config["evidence_packets_path"]),
        "summaries": Path(config["case_summaries_path"]),
        "sar_drafts": Path(config["sar_drafts_path"]),
        "executive_brief": Path(config["executive_brief_path"]),
        "prompts": Path(config["prompt_payloads_path"]),
        "quality": Path(config["grounding_quality_path"]),
    }
    for path in paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    paths["packets"].write_text(
        "".join(json.dumps(item, sort_keys=True, default=str) + "\n" for item in packets),
        encoding="utf-8",
    )
    summaries.to_csv(paths["summaries"], index=False)
    sar_drafts.to_csv(paths["sar_drafts"], index=False)
    paths["executive_brief"].write_text(executive_brief, encoding="utf-8")
    paths["prompts"].write_text(
        "".join(json.dumps(item, sort_keys=True, default=str) + "\n" for item in prompts),
        encoding="utf-8",
    )
    paths["quality"].write_text(json.dumps(quality, indent=2) + "\n", encoding="utf-8")
    report_dir = Path(config["investigation_report_dir"])
    report_dir.mkdir(parents=True, exist_ok=True)
    for case_id, content in notes.items():
        (report_dir / f"{case_id}.md").write_text(content, encoding="utf-8")
    return paths
