# ADR-008: Power BI Semantic Model

## Status
Accepted design; deployment not implemented.

## Context
Executives and operations teams need consistent KPIs, drill-through, access control, and traceable definitions.

## Decision
Use a governed star model with conformed dimensions, narrow facts, explicit measures, single-direction relationships, and reconciliation gates.

## Alternatives Considered
Direct queries to operational outputs produce inconsistent metrics; flat exports are simple but weak for governed analysis.

## Consequences
Dataset ownership, refresh sequencing, measure review, RLS, certification, and lineage become controlled processes.

## Security Implications
Apply Entra groups, workspace roles, RLS/OLS, sensitivity labels, export restrictions, and audit logs.

## Cost Implications
Licensing, capacity, refresh frequency, model size, and concurrency drive cost.

## Local Implementation Mapping
`dashboard/powerbi_data`, DAX examples, semantic specification, KPI definitions, and quality checks implement the contract.

## Azure Production Mapping
Synapse or Fabric serves curated data to a Power BI semantic model and controlled workspaces.
