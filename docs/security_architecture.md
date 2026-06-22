# Security Architecture

This is a target-state design, not a claim of deployed controls or regulatory compliance. The local repository uses synthetic data, no credentials, and no Azure connections.

## Identity and Access

Microsoft Entra ID is the identity authority. Workloads use managed identities; people receive group-based RBAC with least privilege. Privileged roles use PIM, time-bound activation, approval, access reviews, and break-glass accounts. Service principals with secrets are avoided; Key Vault stores unavoidable secrets and certificates with rotation, soft delete, purge protection, logging, and restricted administration.

## Network and Data Protection

Dev, test, and production use separate subscriptions or resource groups, identities, stores, workspaces, and keys. Private endpoints, private DNS, VNet integration, network security groups, firewalls, controlled egress, and disabled public access isolate Event Hubs, ADLS, Synapse, Azure ML, ACR, Key Vault, AI services, and monitoring. Encryption at rest and TLS in transit are mandatory; customer-managed keys are a policy decision based on risk and regulation.

## Workload Controls

Model endpoints require Entra tokens, private access, schema/rate limits, request-size controls, input validation, version telemetry, and abuse monitoring. Power BI uses Entra groups, workspace roles, RLS/OLS, sensitivity labels, export controls, certified datasets, and audit logs. Purview classifies identifiers, predictions, alerts, explanations, narratives, and reporting assets and records ownership and lineage.

## Operations

Diagnostic settings route identity, data-plane, model, AI, pipeline, and administrative events to Log Analytics/SIEM with tamper-resistant retention. Alerts cover privilege changes, denied access, secret operations, unusual extraction, endpoint abuse, alert mutation, and logging gaps. Incident response preserves evidence, contains identities/endpoints, assesses data and model impact, communicates through approved channels, recovers from known-good artifacts, and completes lessons learned.

Security architecture requires formal threat modelling, penetration testing, privacy review, model-risk approval, legal/compliance input, business continuity tests, and periodic control validation before production use.
