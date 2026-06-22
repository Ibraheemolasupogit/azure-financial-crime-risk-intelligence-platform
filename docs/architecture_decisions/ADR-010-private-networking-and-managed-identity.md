# ADR-010: Private Networking and Managed Identity

## Status
Proposed secure deployment baseline.

## Context
Public endpoints and long-lived credentials increase exposure across data, model, AI, and reporting services.

## Decision
Prefer private endpoints, VNet integration, private DNS, disabled public access, managed identities, and RBAC over shared keys.

## Alternatives Considered
Public endpoints with IP allowlists are simpler but broader; service principals with secrets add rotation and leakage risk.

## Consequences
DNS, routing, build agents, service dependencies, break-glass access, and troubleshooting become more complex.

## Security Implications
Least privilege, PIM, access reviews, diagnostic logs, egress controls, and environment isolation remain mandatory.

## Cost Implications
Private endpoints, DNS, firewall, NAT, and private build agents add cost and operational effort.

## Local Implementation Mapping
The project requires no credentials and makes no service calls; `.env` files and caches are ignored.

## Azure Production Mapping
Each supported service receives approved private connectivity and managed identity role assignments through reviewed IaC.
