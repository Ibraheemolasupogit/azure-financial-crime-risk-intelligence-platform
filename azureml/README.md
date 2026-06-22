# Azure Machine Learning Mapping

These YAML files are reference mappings for the synthetic-data platform, not executable deployment configuration. Placeholder workspace assets, compute names, model versions, datastore URIs, inference code, environment versions, identities, and network settings must be supplied through an approved deployment process.

| Local artifact | Azure ML concept |
| --- | --- |
| `scripts/build_features.py` | Reusable feature-engineering component |
| `scripts/train_fraud_baseline.py` | Command component/job on managed compute |
| `models/fraud_baseline_pipeline.joblib` | Versioned registered model after approval |
| Metrics and threshold outputs | Evaluation evidence and registration gate |
| `scripts/explain_fraud_model.py` | Explanation/evaluation component |
| Monitoring outputs | Azure ML/Monitor data, prediction, and performance controls |
| Batch job mapping | Scheduled batch scoring against curated data |
| Managed endpoint YAML | AAD-authenticated, private online scoring endpoint |

Productionisation requires pinned dependencies, approved base images, input/output bindings, model signature validation, dedicated inference code, managed identity, private endpoints, autoscaling, load tests, deployment approvals, blue/green traffic controls, monitoring, and rollback. No Azure CLI commands or workspace identifiers are included.
