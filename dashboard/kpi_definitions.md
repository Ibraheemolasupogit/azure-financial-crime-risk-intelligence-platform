# KPI Definitions

All KPIs are synthetic portfolio measures refreshed after the complete local pipeline. Counts exclude no valid generated rows; rates use `DIVIDE` semantics to avoid division by zero.

| KPI | Business and technical definition | Numerator / denominator | Grain and sources | Interpretation, limitation, visual |
| --- | --- | --- | --- | --- |
| KPI001 Total Customers | Distinct scored customers | Distinct customer keys | Portfolio; fact_customer_risk | Synthetic population size; card |
| KPI002 Total Accounts | Distinct analytical accounts | Distinct account keys | Portfolio; dim_account | Generated account footprint; card |
| KPI003 Total Transactions | Transaction fact rows | Row count | Portfolio/date; fact_transactions | Synthetic activity volume; card/trend |
| KPI004 Total Transaction Value | Sum transaction amount | Amount sum | Portfolio/date/currency; fact_transactions | Mixed synthetic currencies are not FX-normalised; card/trend |
| KPI005 Fraud Prevalence | Synthetic positive labels / evaluated predictions | Actual positives / predictions | Test prediction grain; fact_fraud_predictions | Retrospective synthetic outcome only; percentage card |
| KPI006 Predicted Fraud Count | Predicted-positive transactions | Predicted label = 1 | Prediction grain; fact_fraud_predictions | Threshold-dependent workload; card |
| KPI007–010 Fraud Precision/Recall/F1/AP | Standard classification measures | Confusion counts or ranked labels | Evaluation period; agg_fraud_performance | Weak synthetic signal; KPI cards |
| KPI011 False Positives | Predicted positive with actual synthetic label 0 | FP count | Prediction grain | Operational burden; alert card |
| KPI012 Total AML Alerts | AML fact rows | Row count | Alert grain; fact_aml_alerts | Rules may generate multiple alerts per transaction; card/trend |
| KPI013 Alerted Transaction Rate | Distinct alerted transactions / all transactions | Distinct transaction keys | Portfolio; AML and transaction facts | Threshold-tuning indicator; gauge |
| KPI014 Affected AML Customers | Distinct AML customer keys | Distinct customer keys | Portfolio; fact_aml_alerts | Synthetic customer coverage; card |
| KPI015 High Severity Alerts | High or critical AML alerts | Filtered alert count | Alert grain | Triage volume; stacked column |
| KPI016 High/Critical Risk Customers | Customers in high or critical band | Filtered customers | Customer grain; fact_customer_risk | Analytical categorisation, not legal conclusion; card |
| KPI017 Urgent/Enhanced Reviews | Customers with urgent or enhanced priority | Filtered customers | Customer grain | Human-review queue; card |
| KPI018 Investigation Cases | Generated case rows | Row count | Case grain; fact_investigation_cases | Deterministic draft workload; card |
| KPI019–020 Monitoring Warnings/Critical | Monitoring alerts by status | Filtered alert count | Control-alert grain | Control health; status cards |
| KPI021 Overall Platform Status | Aggregated monitoring status | Highest applicable status | Portfolio; monitoring summary | Synthetic control status; traffic-light card |

Refresh expectation is after every complete local run. Metric changes require owner review, version control, reconciliation testing, and updated semantic/DAX documentation.
