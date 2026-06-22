# Monitoring And Drift Detection

Milestone 10 provides deterministic local monitoring across data quality, numeric and categorical drift, fraud performance, AML operations, customer risk, explainability, GenAI safety, and pipeline health.

Earlier chronological transactions form the baseline period and later transactions form the current period. Customer-level artifacts lack historical snapshots, so their distribution comparison uses a documented deterministic portfolio split. This is a production-monitoring simulation, not a claim of temporal customer drift.

Numeric drift uses Population Stability Index with safe constant handling. Categorical drift uses total variation distance plus new-category and dominant-category checks. Fraud monitoring reports threshold metrics and handles periods without positive labels. AML monitoring explicitly measures alert coverage, alert-to-transaction ratio, customer saturation, rule concentration, zero-volume rules, and duplicates.

Risk monitoring checks score distributions, bands, versions, dominant components, and contribution reconstruction. Explainability and GenAI integrity failures are critical, including reconstruction failures, excluded features, unsupported claims, missing disclaimers, or enabled network payloads. Pipeline controls check expected artifacts, size, parseability, and freshness.

Overall status is `critical` for mandatory integrity or safety failures, `unavailable` for missing required controls, `warning` for material drift, performance, volume, or freshness findings, and `healthy` otherwise. Monitoring only recommends human investigation; model retraining and changes to thresholds, AML rules, weights, or bands require controlled approval.

Run `python3 scripts/run_platform_monitoring.py`. Conceptually, outputs map to Azure Monitor, Application Insights, Azure ML monitoring and registry, ADLS, Synapse, Purview, AI Foundry observability, Azure OpenAI monitoring, Log Analytics, and Power BI. No cloud calls occur.
