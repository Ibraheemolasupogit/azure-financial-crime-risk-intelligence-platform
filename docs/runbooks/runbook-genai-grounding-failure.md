# Runbook: GenAI Grounding Failure

## Trigger
Unsupported claim, incorrect reference, accusatory wording, prompt injection, missing disclaimer, or safety control failure.

## Severity
High for investigator-facing misinformation; critical if an unsafe narrative leaves the controlled workflow.

## Initial Checks
Confirm evidence packet, prompt/template/model version, retrieval sources, output, validators, and reviewer action.

## Containment
Disable affected generation route, quarantine outputs, require manual drafting, revoke unsafe documents, and preserve evidence.

## Investigation
Classify source quality, prompt injection, retrieval, model behaviour, validator gap, or reviewer/process failure.

## Remediation
Tighten structured inputs, allowlists, templates, validators, content policy, or model configuration through approval.

## Validation
Run adversarial and regression cases, citation/number checks, language policy, privacy, and human evaluation.

## Escalation
Investigation owner, Responsible AI, Security, Privacy/Legal, Compliance, and incident command if disclosed.

## Evidence to Retain
Minimised prompt, sources, output, versions, safety results, reviewer decision, access/audit logs.

## Post-Incident Review
Update threat model, red-team suite, reviewer guidance, and permitted use cases.
