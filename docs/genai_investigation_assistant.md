# GenAI Investigation Assistant

Milestone 9 converts structured synthetic fraud, AML, customer-risk, and model-explanation evidence into investigator-ready drafts. The default `deterministic_template` mode uses validated templates and makes no model or network request.

`azure_openai_placeholder` creates the same safe prompt payload, marks `network_call_enabled` false, and falls back to deterministic generation. It documents a future Azure AI Foundry integration without adding SDKs, credentials, or external data transfer.

## Evidence And Selection

At most five customers are selected deterministically using configured risk bands, review priorities, scores, AML alert counts, and fraud probabilities. Packets contain identifiers, component scores, top AML evidence, model probabilities, reason codes, quality status, timestamps, and source references. Names, birth dates, addresses, and other unnecessary details are excluded.

## Outputs And Safety

The assistant creates case summaries, Markdown review notes, training-only SAR-style drafts, an executive briefing, disabled provider payloads, and grounding-quality results. Drafts separate observed facts, analytical indicators, uncertainty, and recommended human checks.

Validation checks numbers, transaction and AML references, prohibited claims, disclaimers, word limits, synthetic-data language, and human-review language. Failures produce a non-zero CLI status. Drafts never establish intent or wrongdoing, submit a report, or recommend automatic adverse action.

Run locally:

```bash
python3 scripts/generate_investigation_reports.py
```

## Limitations And Azure Mapping

Templates can be incomplete, repetitive, or overemphasise noisy upstream controls. Human review and source verification remain mandatory. Conceptually, orchestration maps to Azure AI Foundry and Functions, future controlled generation to Azure OpenAI, filtering to Azure AI Content Safety, model evidence to Azure Machine Learning, storage to ADLS, analysis to Synapse, secrets to Key Vault, lineage to Purview, telemetry to Azure Monitor, and reporting to Power BI. No Azure services are called.
