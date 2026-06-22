# Fraud Model Explainability

Milestone 8 explains the persisted fraud Logistic Regression pipeline without retraining or replacing it. Explainability helps reviewers understand model behaviour, challenge false positives, verify feature lineage, and audit how an individual synthetic transaction received its score.

Explanations describe model associations. They do not establish causation, customer intent, fraud, or criminal conduct.

## Global And Local Explanations

Global explanations rank signed Logistic Regression coefficients for all transformed numeric and one-hot features. A second view aggregates absolute coefficient magnitude to the 34 source features for portfolio-level interpretation.

Local explanations use the exact transformed feature vector for each held-out transaction:

```text
feature contribution = transformed feature value × coefficient
decision score = intercept + sum(feature contributions)
probability = logistic(decision score)
```

All transformed contributions are retained, including zero-valued one-hot terms, so a reviewer can reconstruct the decision mathematically.

## Categorical Feature Aggregation

One-hot encoded levels remain separate model terms because each has its own coefficient. The engine maps them back to source fields such as `channel`, `merchant_country`, or `ip_country` for readable summaries while preserving transformed names in detailed outputs.

## Reason Codes

For each transaction, the largest positive and negative contributions above the configured minimum become deterministic reason codes. Reason records retain the source feature, observed value, signed contribution, model probability, selected threshold, human-readable text, and non-causal caveat.

Positive reasons increase the model decision score; negative reasons reduce it. A reason does not imply the feature is inherently suspicious or safe.

## Quality Validation

Every explanation checks that:

- the transformed vector exists;
- contributions are finite;
- contributions plus intercept reproduce the decision score;
- the logistic transform reproduces model probability;
- reason codes reference valid model features;
- identifiers, timestamps, labels, and outcomes are excluded;
- JSON evidence and rankings are deterministic.

Critical reconstruction failures make the CLI return a non-zero status.

## Investigator Packets And False Positives

A small deterministic sample covers the highest and lowest probabilities and available true-positive, false-positive, true-negative, and false-negative outcomes without duplication. Empty outcome groups are handled safely.

The current synthetic model has many false positives. Their explanations reveal which model associations produced elevated scores; explanations do not make those predictions correct. Reviewers must consider source data, context, plausible legitimate activity, data quality, and known model limitations.

## Outputs

- `outputs/fraud_global_feature_importance.csv`
- `outputs/fraud_global_source_feature_importance.csv`
- `outputs/fraud_local_explanations.csv`
- `outputs/fraud_feature_contributions.csv`
- `outputs/fraud_prediction_reason_codes.csv`
- `outputs/fraud_explanation_quality.json`
- `outputs/fraud_explanations_by_error_type.csv`
- `outputs/fraud_explainability_summary.json`
- `reports/fraud_model_explainability_report.md`
- `reports/investigator_explanations/`

Run locally:

```bash
python3 scripts/explain_fraud_model.py
```

## Azure Conceptual Mapping

| Local capability | Azure-aligned concept |
| --- | --- |
| Native interpretation and quality checks | Azure Machine Learning responsible AI capabilities |
| Model-version linkage | Azure Machine Learning model registry |
| Contribution and reason outputs | Azure Data Lake Storage |
| Portfolio explanation analysis | Azure Synapse Analytics |
| Pipeline telemetry | Azure Monitor and Application Insights |
| Feature lineage and governance | Microsoft Purview |
| Explanation dashboards | Power BI |
| Later investigator assistance | Azure AI Foundry |

These are conceptual mappings only. No Azure credentials or services are used.
