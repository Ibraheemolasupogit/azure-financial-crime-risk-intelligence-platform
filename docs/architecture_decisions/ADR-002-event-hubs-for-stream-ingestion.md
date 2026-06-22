# ADR-002: Event Hubs for Stream Ingestion

## Status
Proposed Azure deployment mapping.

## Context
Transaction events require partitioned, replayable, high-throughput ingestion with independent consumers.

## Decision
Use Azure Event Hubs as the streaming ingress, partitioned by stable account identifier and consumed through dedicated consumer groups.

## Alternatives Considered
Service Bus better suits commands and workflows; Kafka management adds operational burden; direct HTTP ingestion weakens replay.

## Consequences
Event ordering is partition-scoped, consumers must checkpoint, and schema compatibility must be governed.

## Security Implications
Use private endpoints, Entra authentication, managed identities, least-privilege data roles, and avoid connection strings.

## Cost Implications
Throughput units, retention, capture, and egress drive cost; autoscaling and batching need measurement.

## Local Implementation Mapping
`transactions.jsonl` represents an ordered event stream loaded by the ingestion module.

## Azure Production Mapping
Event Hubs Capture lands immutable events in ADLS; Stream Analytics or Functions validate and route them.
