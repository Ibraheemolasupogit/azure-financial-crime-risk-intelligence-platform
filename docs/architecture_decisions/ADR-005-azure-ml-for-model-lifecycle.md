# ADR-005: Azure ML for the Model Lifecycle

## Status
Proposed Azure deployment mapping.

## Context
Fraud models require reproducible training, registration, approval, deployment, explanation, monitoring, and rollback.

## Decision
Map local sklearn scripts to Azure ML environments, components, pipelines, registry versions, batch jobs, and managed endpoints.

## Alternatives Considered
Custom Kubernetes offers control but greater burden; Functions suit lightweight inference but not the complete model lifecycle.

## Consequences
Environment pinning, artifact lineage, approval gates, compute governance, and endpoint SLOs become formal controls.

## Security Implications
Use managed identity, private workspace/endpoints, approved images, ACR scanning, encrypted stores, and authenticated inference.

## Cost Implications
Training compute, idle endpoint replicas, batch compute, registry storage, and monitoring drive cost.

## Local Implementation Mapping
`train_fraud_baseline.py`, persisted joblib, metadata, metrics, explanations, and monitoring provide reproducible evidence.

## Azure Production Mapping
The `azureml/` examples map these artifacts to command jobs, components, pipeline, registry, and endpoints.
