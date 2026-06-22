# Infrastructure Reference Scaffold

This directory contains illustrative Bicep for an Azure-aligned deployment of the synthetic-data platform. It is not executed by local scripts or CI, provisions nothing, and contains no credentials. `main.bicep` uses subscription scope to create a resource group and references modular service definitions.

## Security Defaults

Public access and shared-key authentication are disabled where represented; managed identities, RBAC-enabled Key Vault, TLS, purge protection, hierarchical namespace, private networking, and central logs are preferred. Private endpoints, DNS zones, role assignments, alert destinations, Synapse credentials, Purview scans, and workload-specific policies remain documented placeholders because they require tenant-specific IDs and approvals.

## Before Any Real Deployment

Review service availability, naming uniqueness, regional support, quotas, Azure Policy, cost budgets, data residency, network topology, RBAC, managed private endpoints, customer-managed key requirements, and separation of dev/test/prod. Validate with the Azure Bicep compiler and security tooling in an authorised subscription pipeline. No deployment command is included.

Run only the repository's local static validator:

```bash
python3 scripts/validate_infrastructure.py
```
