# ADR-001: Local-First Development

## Status
Accepted for portfolio implementation.

## Context
The platform must be reproducible without cloud accounts, costs, regulated data, or network access.

## Decision
Implement every analytical capability locally against deterministic synthetic data, then document Azure equivalents separately.

## Alternatives Considered
Azure-only development was rejected because it reduces accessibility and introduces credentials and cost. Mocking every Azure SDK was rejected as needless complexity.

## Consequences
Reviewers can execute the full pipeline; cloud performance and service integration remain unproven.

## Security Implications
No cloud secrets are needed. Local outputs still require appropriate workstation controls.

## Cost Implications
Local execution has no service consumption cost; compute is borne by the developer workstation.

## Local Implementation Mapping
Python CLIs, files, pytest, Ruff, and deterministic templates implement the pipeline.

## Azure Production Mapping
Event Hubs, ADLS, Synapse, Azure ML, AI Foundry, Monitor, Purview, and Power BI replace local boundaries after formal design review.
