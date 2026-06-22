# ADR-004: Synapse for Analytics

## Status
Proposed Azure deployment mapping.

## Context
Historical AML, fraud, risk, and executive analytics require governed joins over lake data.

## Decision
Use Synapse serverless SQL initially for exploration and serving; consider dedicated capacity only after workload evidence.

## Alternatives Considered
Fabric may suit organisations standardised on it; Databricks is strong for lakehouse engineering; a standalone database may suit smaller workloads.

## Consequences
SQL models, workload management, data distribution, and semantic refresh contracts require ownership.

## Security Implications
Use managed identities, managed VNet, private endpoints, row/object controls, audit logs, and separated workspaces.

## Cost Implications
Serverless scanned bytes and dedicated capacity are distinct cost models; curated partitioned files reduce scans.

## Local Implementation Mapping
Pandas transformations and governed CSV facts/aggregates simulate analytical preparation.

## Azure Production Mapping
Synapse reads curated ADLS data, prepares feature/reporting views, and serves Power BI and AML analysis.
