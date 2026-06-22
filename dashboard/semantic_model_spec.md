# Semantic Model Specification

## Tables And Grains

- Dimensions: `dim_customer`, `dim_account`, `dim_date`, `dim_time`, `dim_aml_rule`, `dim_risk_band`, and `dim_monitoring_control` contain one row per business entity or classification member.
- Facts: `fact_transactions`, `fact_fraud_predictions`, `fact_aml_alerts`, `fact_customer_risk`, `fact_risk_components`, `fact_model_explanations`, `fact_investigation_cases`, `fact_monitoring_alerts`, and `fact_pipeline_health` preserve their declared transaction, alert, score, explanation, case, or control grain.
- Aggregates: `agg_executive_kpis`, `agg_fraud_performance`, `agg_aml_operations`, `agg_customer_risk_distribution`, `agg_monitoring_health`, and `agg_investigation_workload` provide governed presentation-ready summaries.

## Relationships

Use single-direction one-to-many filters from dimensions to facts. `dim_customer` filters transaction, fraud, AML, risk, component, explanation, and case facts. `dim_account` filters transactions and AML alerts. `dim_date` filters transaction date, alert date, scoring date, monitoring date, and pipeline date as role-playing date relationships. `dim_time` filters transactions. `dim_aml_rule` filters AML alerts. Avoid bidirectional filtering.

Primary keys are dimension surrogate keys. Fact foreign keys use deterministic matching keys. Hide technical keys and retain natural IDs only for drill-through. Designate `dim_date[full_date]` as the date table.

## Formatting And Summarisation

- Amount: configured currency display; do not sum mixed currencies without a currency filter.
- Probability and percentages: four decimals or percentage format.
- Scores: two decimals, bounded 0–100.
- Keys, IDs, labels, statuses, and ranks: do not summarise.
- Contributions and risk points: sum where contextually appropriate.

Recommended hierarchies: Date Year > Quarter > Month > Date; Customer > Account > Transaction; AML Rule > Severity > Alert. Drill-through targets are customer risk, transaction explanation, AML alert, investigation case, and monitoring control.

## Security And Refresh

Conceptual RLS may restrict investigators by assigned portfolio or region; object-level security may hide technical identifiers and model internals. No security is implemented in CSV files. Refresh order follows dimensions, facts, aggregates, then semantic validation. Future incremental refresh should partition transaction, alert, prediction, and monitoring facts by date.
