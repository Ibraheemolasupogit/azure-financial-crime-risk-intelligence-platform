"""Structured prompt templates for future controlled model integration."""

SYSTEM_CONSTRAINTS = (
    "Use only the supplied structured synthetic evidence. Use neutral language. Do not invent "
    "facts, infer intent, make legal conclusions, or accuse a customer of wrongdoing. Distinguish "
    "observations, analytical indicators, uncertainty, and recommended human review. Include the "
    "required human-review and synthetic-data disclaimers."
)

CASE_SUMMARY_TEMPLATE = (
    "Create a concise case summary with sections for observed facts, analytical indicators, "
    "uncertainties, and recommended investigator checks. Evidence: {evidence_json}"
)

INVESTIGATOR_NOTE_TEMPLATE = (
    "Create an investigator review note with case overview, transaction indicators, AML rules, "
    "model indicators, explanation factors, evidence table, uncertainties, benign explanations, "
    "checks, limitations, and required disclaimers. Evidence: {evidence_json}"
)

SAR_STYLE_TEMPLATE = (
    "Create a neutral training-only SAR-style draft based solely on supplied evidence. Label it "
    "not for submission, state uncertainties, require investigator validation, and avoid "
    "conclusions about intent or offences. Evidence: {evidence_json}"
)

EXECUTIVE_BRIEF_TEMPLATE = (
    "Summarise selected synthetic cases, risk bands, review priorities, dominant AML rules and "
    "risk components, model limitations, false-positive concerns, operational risks, control "
    "reviews, and human-review dependency. Evidence: {evidence_json}"
)


def expected_case_output_schema() -> dict[str, str]:
    """Return the future provider's constrained output contract."""
    return {
        "observed_facts": "string",
        "analytical_indicators": "string",
        "uncertainties": "string",
        "recommended_human_checks": "array[string]",
        "disclaimers": "array[string]",
    }
