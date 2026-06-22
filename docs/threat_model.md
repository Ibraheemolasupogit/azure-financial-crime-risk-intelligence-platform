# Threat Model

## Scope and Assets

Assets include transaction events, customer/account pseudonymous identifiers, features, rule configuration, model artifacts, endpoints, predictions, risk scores, alerts, explanations, investigation narratives, dashboard datasets, credentials, logs, lineage, and approval evidence.

Trust boundaries exist between producers and Event Hubs, streaming and lake zones, data and ML workspaces, endpoint callers, GenAI prompts/model, case systems, Power BI, CI/CD, and privileged administration. Threat actors include external attackers, malicious insiders, compromised workloads, over-privileged analysts, supply-chain attackers, and accidental operators. Entry points include event ingestion, files, APIs, model endpoints, prompts, dashboards, pipelines, package dependencies, and administrative planes.

## STRIDE Analysis

| Threat | Category | Primary mitigations | Residual risk / monitoring |
| --- | --- | --- | --- |
| Spoofed producer or event | Spoofing | Entra/managed identity, private endpoints, schema and provenance checks | Compromised identity; monitor producer/partition anomalies |
| Poisoned transaction data | Tampering | Immutable raw zone, hashes, validation, quarantine, lineage | Plausible malicious values; drift and source-quality alerts |
| Malicious feature manipulation | Tampering | Versioned code/config, PR approval, prior-only tests, feature validation | Collusion or subtle manipulation; distribution and lineage monitoring |
| Alert or threshold tampering | Tampering/repudiation | RBAC, signed releases, immutable evidence, change approvals | Privileged misuse; audit and alert-volume monitoring |
| Missing decision evidence | Repudiation | Correlation IDs, model/rule/config versions, retained logs | Storage/log failure; pipeline-health controls |
| Dashboard data leakage | Information disclosure | RLS/OLS, labels, export controls, minimised facts | Screenshots/authorised misuse; access and export audit |
| Model theft | Information disclosure | Private registry/endpoint, no artifact download for consumers, ACR controls | Query extraction; rate, entropy, and usage monitoring |
| Secret exposure | Information disclosure | Managed identity, Key Vault, secret scanning, rotation | Build logs or operator error; SIEM and emergency rotation |
| Endpoint abuse or denial | DoS | AAD, quotas, rate limits, WAF/API gateway, autoscaling | Cost exhaustion/adversarial load; latency and spend alerts |
| Prompt injection | Spoofing/tampering | Structured evidence, instruction separation, allowlisted sources, output validation | Novel injection; safety evaluation and reviewer rejection rates |
| Generated-narrative misuse | Elevation/repudiation | Non-accusatory templates, disclaimers, human approval, no autonomous filing | Copying outside workflow; DLP and review audit |
| Privilege escalation | Elevation | Least privilege, PIM, access reviews, conditional access | Tenant compromise; identity protection and role-change alerts |
| Lineage gaps | Repudiation/tampering | Purview, manifests, quality gates, model metadata | Connector failure; completeness controls |

## Response Priorities

Contain compromised identities and endpoints, preserve immutable evidence, identify affected data/model/config versions, assess decisions and reports, invoke rollback, reprocess from trusted raw events, notify governance owners, and document residual risk. This model must be revisited for each real deployment topology and data classification.
