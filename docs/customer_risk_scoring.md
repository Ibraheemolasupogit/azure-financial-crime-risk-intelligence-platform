# Customer Risk Scoring

Milestone 7 combines synthetic customer, behavioural, AML, fraud-model, and device/session indicators into a transparent analytical score for investigation prioritisation. The score does not prove criminal activity and must not independently trigger account closure, reporting, sanctions, or any adverse or legal decision.

## Components And Formula

Each component is capped and normalised to a 0–100 scale. The configured total is:

```text
total_risk_score =
    0.20 × kyc_risk_score
  + 0.20 × transaction_behaviour_score
  + 0.30 × aml_alert_score
  + 0.15 × fraud_model_score
  + 0.15 × device_session_score
```

Weights are validated to sum to 1.0. Component contributions are rounded and summed directly, allowing `customer_risk_components.csv` to reconstruct each total.

### Customer And KYC

Uses configured mappings for KYC status, synthetic customer risk rating, PEP status, sanctions-screening status, AML watchlist exposure, customer tenure, and onboarding recency.

### Transaction Behaviour

Uses threshold-relative transaction volume and value, maximum amount, cross-border ratio, failed and night transaction ratios, merchant-country diversity, new-device activity, and maximum historical velocity.

### AML Alert Exposure

Uses alert totals, distinct rules, severity counts, configured rule points, maximum severity, and high-value, structuring, geography, device/session, and KYC/watchlist alert groups.

### Fraud Model

Uses only fraud probabilities and class predictions: maximum and average probability, predicted-positive count and ratio, and high-probability count and ratio. Actual fraud labels and prediction error types are excluded.

### Device And Session

Uses risky and elevated session counts, new-device transactions, failed authentication, geography mismatch, and distinct devices.

## Bands And Priorities

Scores receive a configurable `low`, `moderate`, `high`, or `critical` analytical band and a `routine`, `standard`, `enhanced`, or `urgent` review priority. Bands describe configured risk indicators; priorities help sequence human investigation. Neither is a legal determination or sufficient basis for adverse action.

## Evidence And Reasons

Every customer receives deterministic primary and secondary reasons plus valid JSON evidence. The audit output contains one row per customer per component with raw measures, thresholds, normalised score, weight, weighted contribution, cap, reason, and evidence.

Outputs contain customer identifiers and risk indicators only. Synthetic names, dates of birth, and unnecessary profile details are excluded.

## Label Separation And Retrospective Evaluation

Historical fraud columns are removed when customer features are loaded, and the scoring function rejects actual or historical fraud-label columns. The fraud scoring component consumes model outputs only.

After scores are complete, a separate retrospective evaluator compares bands with synthetic historical labels. This does not feed back into scores. Because labels are synthetic and weakly related to behaviour, the comparison is not robust validation.

## Outputs

- `outputs/customer_risk_scores.csv`: customer scores, bands, reasons, and selected indicators
- `outputs/customer_risk_components.csv`: reconstructable five-component audit trail
- `outputs/customer_risk_summary.json`: portfolio distribution and configuration status
- `outputs/customer_risk_retrospective_evaluation.json`: separate label-based review
- `reports/customer_risk_scoring_report.md`: methodology and portfolio report

Run locally:

```bash
python3 scripts/score_customer_risk.py
```

## Limitations And Tuning

The framework combines correlated signals: AML alerts may already reflect device, geography, KYC, and transaction behaviour. Weights and caps therefore require sensitivity analysis and review for double counting. Broad AML controls can propagate false positives into customer scores. Thresholds should be tested against investigation capacity, customer impact, temporal stability, and subgroup error rates.

## Azure Conceptual Mapping

| Local capability | Azure-aligned concept |
| --- | --- |
| Source features and score outputs | Azure Data Lake Storage |
| Customer-level aggregation | Azure Synapse Analytics |
| Later learned risk models | Azure Machine Learning |
| Scoring orchestration | Azure Functions |
| Later investigator assistance | Azure AI Foundry |
| Lineage, classification, governance | Microsoft Purview |
| Scoring telemetry | Azure Monitor and Application Insights |
| Customer risk reporting | Power BI |
| Deployed configuration secrets | Azure Key Vault |

These mappings are conceptual only. No Azure resources or credentials are used.
