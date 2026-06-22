# ADR-009: Purview for Governance

## Status
Proposed Azure deployment mapping.

## Context
Financial-crime assets require discoverability, ownership, classification, lineage, retention, and audit evidence.

## Decision
Use Microsoft Purview as the catalogue and lineage plane while source systems retain enforcement responsibilities.

## Alternatives Considered
Documentation-only governance becomes stale; custom catalogues add maintenance; third-party tools may be appropriate where already standard.

## Consequences
Scanning schedules, collections, glossary terms, lineage connectors, stewardship, and exception handling need operating processes.

## Security Implications
Limit scan credentials and collection roles, use private access where supported, and classify sensitive attributes and model outputs.

## Cost Implications
Data map capacity, scans, processing, and retention are cost drivers; scope and cadence should follow risk.

## Local Implementation Mapping
Data dictionaries, lineage matrix, validation reports, model metadata, and output manifests provide inspectable lineage evidence.

## Azure Production Mapping
Purview scans ADLS, Synapse, Azure ML, and Power BI and records glossary, classifications, owners, and lineage.
