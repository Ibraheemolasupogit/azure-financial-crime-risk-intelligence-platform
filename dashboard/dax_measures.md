# DAX Measure Specification

```DAX
Total Transactions = COUNTROWS(fact_transactions)
Total Transaction Value = SUM(fact_transactions[transaction_amount])
Predicted Fraud Transactions = CALCULATE(COUNTROWS(fact_fraud_predictions), fact_fraud_predictions[predicted_fraud_label] = 1)
Fraud Prevalence = DIVIDE(CALCULATE(COUNTROWS(fact_fraud_predictions), fact_fraud_predictions[actual_synthetic_fraud_label] = 1), COUNTROWS(fact_fraud_predictions))
Fraud Precision = DIVIDE(CALCULATE(COUNTROWS(fact_fraud_predictions), fact_fraud_predictions[error_type] = "true_positive"), CALCULATE(COUNTROWS(fact_fraud_predictions), fact_fraud_predictions[error_type] IN {"true_positive", "false_positive"}))
Fraud Recall = DIVIDE(CALCULATE(COUNTROWS(fact_fraud_predictions), fact_fraud_predictions[error_type] = "true_positive"), CALCULATE(COUNTROWS(fact_fraud_predictions), fact_fraud_predictions[error_type] IN {"true_positive", "false_negative"}))
Fraud F1 = DIVIDE(2 * [Fraud Precision] * [Fraud Recall], [Fraud Precision] + [Fraud Recall])
False Positive Rate = DIVIDE(CALCULATE(COUNTROWS(fact_fraud_predictions), fact_fraud_predictions[error_type] = "false_positive"), CALCULATE(COUNTROWS(fact_fraud_predictions), fact_fraud_predictions[error_type] IN {"false_positive", "true_negative"}))
Total AML Alerts = COUNTROWS(fact_aml_alerts)
Alerted Transaction Rate = DIVIDE(DISTINCTCOUNT(fact_aml_alerts[transaction_key]), [Total Transactions])
Affected Customers = DISTINCTCOUNT(fact_aml_alerts[customer_key])
High Severity Alerts = CALCULATE([Total AML Alerts], fact_aml_alerts[severity] IN {"high", "critical"})
Average Customer Risk Score = AVERAGE(fact_customer_risk[total_risk_score])
High or Critical Risk Customers = CALCULATE(DISTINCTCOUNT(fact_customer_risk[customer_key]), fact_customer_risk[risk_band] IN {"high", "critical"})
Urgent Review Cases = CALCULATE(COUNTROWS(fact_investigation_cases), fact_investigation_cases[review_priority] = "urgent")
Monitoring Warnings = CALCULATE(COUNTROWS(fact_monitoring_alerts), fact_monitoring_alerts[status] = "warning")
Monitoring Critical Alerts = CALCULATE(COUNTROWS(fact_monitoring_alerts), fact_monitoring_alerts[status] = "critical")
Explanation Pass Rate = DIVIDE(CALCULATE(COUNTROWS(fact_model_explanations), fact_model_explanations[explanation_status] = "passed"), COUNTROWS(fact_model_explanations))
Grounding Pass Rate = DIVIDE(CALCULATE(COUNTROWS(fact_investigation_cases), fact_investigation_cases[grounding_status] = "passed"), COUNTROWS(fact_investigation_cases))
Pipeline Healthy Stage Rate = DIVIDE(CALCULATE(COUNTROWS(fact_pipeline_health), fact_pipeline_health[stage_status] = "healthy"), COUNTROWS(fact_pipeline_health))
```

Percentage measures should use percentage formatting. `DIVIDE` prevents divide-by-zero failures. Measures respond to dimension filter context. All results are synthetic and must not be presented as institutional performance.
