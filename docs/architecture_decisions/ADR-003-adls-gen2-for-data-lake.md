# ADR-003: ADLS Gen2 for the Data Lake

## Status
Proposed Azure deployment mapping.

## Context
Raw, validated, feature, prediction, explanation, and reporting artifacts need durable zoned storage and lineage.

## Decision
Use ADLS Gen2 with hierarchical namespace and separate raw, validated, curated, model, and reporting zones.

## Alternatives Considered
Database-only storage limits replay; standard Blob lacks filesystem semantics; local disks are not shared or durable.

## Consequences
Lifecycle, partition, small-file, schema, and access policies become explicit platform responsibilities.

## Security Implications
Disable public/shared-key access; use private endpoints, managed identities, RBAC/ACLs, encryption, and diagnostic logs.

## Cost Implications
Capacity, transaction volume, redundancy, tiering, retention, and egress are primary drivers.

## Local Implementation Mapping
`data/raw`, `data/processed`, `outputs`, and `dashboard/powerbi_data` simulate storage zones.

## Azure Production Mapping
ADLS containers and folders implement zones, with Purview scans and Synapse/Azure ML managed access.
