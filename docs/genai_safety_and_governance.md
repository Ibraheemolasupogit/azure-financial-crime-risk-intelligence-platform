# GenAI Safety And Governance

## Intended And Prohibited Use

The assistant supports synthetic evidence review, investigation drafting, control testing, and portfolio demonstration. It must not accuse customers, establish intent, make legal conclusions, submit regulatory reports, automate account actions, or replace qualified investigators.

## Oversight And Grounding

Every output requires human review and must remain grounded in versioned structured evidence. Numeric claims, rules, and transaction references are validated. Required disclaimers distinguish synthetic analytical drafts from official records.

## Hallucination And Prompt-Injection Controls

Default generation is deterministic and does not interpret free-form external content. Future prompts treat evidence as data, use fixed system constraints and output schemas, prohibit instruction-following from evidence fields, disable tools, and require output validation before publication.

## Data Protection And Access

Packets minimise data to synthetic identifiers and risk evidence. A deployed system would require confidentiality classification, least privilege, encryption, Key Vault secrets, retention rules, access logging, and controlled exports.

## Audit, Versioning, And Validation

Record evidence sources, configuration, templates, output version, generated timestamp, case ID, provider setting, and safety results. Prompt, model, threshold, and template changes require review, testing, approval, and rollback capability.

## Incidents And Red-Team Scenarios

Stop publication after unsupported claims, missing disclaimers, leaked personal data, prompt injection, fabricated identifiers, unsafe recommendations, or grounding failures. Preserve artifacts, assess impact, notify owners, remediate, retest, and document resolution. Red-team testing should cover accusatory language, hidden instructions, data exfiltration, false certainty, biased narratives, and submission simulation.

## False Positives And Legal Boundary

Upstream model and AML false positives can produce persuasive but incorrect drafts. A coherent narrative does not validate an alert. Investigator context and documented disposition are essential. This project creates no real SAR and claims no regulatory certification.

All data, identities, alerts, labels, and generated artifacts are synthetic.
