# Fraud Detection Baseline Model

Milestone 5 trains a local supervised fraud-classification baseline from the validated transaction feature table. The objective is to establish an auditable modelling workflow for an imbalanced financial-crime use case, not to claim production-grade detection performance.

## Target And Features

The supervised target is the synthetic binary `fraud_label`. Predictive inputs are selected from `data/processed/transaction_features.csv` with support from the feature dictionary.

The pipeline excludes transaction, account, customer, device, and session identifiers; the raw timestamp; fraud labels and label metadata; current transaction status; configured exclusions; and any feature dictionary entry classified as a label or high leakage risk. The final feature list is saved as `outputs/fraud_feature_list.json`.

## Chronological Evaluation

Transactions are sorted by timestamp. The earliest 75% form the training partition and the latest 25% form the test partition. This more closely reflects a fraud system trained on historical activity and evaluated on later events than a random split would. The split rejects invalid timestamps, empty partitions, very small datasets, single-class targets, and partitions without positive fraud examples.

## Baseline Pipeline

The sklearn `Pipeline` contains a `ColumnTransformer` and balanced Logistic Regression:

- Numeric columns use median imputation and standard scaling.
- Categorical columns use most-frequent imputation and one-hot encoding with unknown-category handling.
- Logistic Regression uses balanced class weights and deterministic configuration.

This transparent baseline establishes a reference point for later model development. No tree ensemble, anomaly model, SHAP analysis, AML rule engine, or customer risk model is included.

## Threshold And Metrics

Candidate probability thresholds are compared using precision, recall, F1, and predicted alert volume. The configured default chooses the highest F1 threshold. Recall subject to minimum precision is also supported.

Threshold selection uses the held-out evaluation partition for demonstration. A production workflow should reserve a separate validation period or use time-aware cross-validation, then perform one final test evaluation.

Accuracy is reported only as a secondary measure. The primary review focuses on recall, precision, F1, average precision, ROC AUC, false-positive rate, false-negative rate, and confusion-matrix counts. In fraud operations, missed fraud has financial and customer consequences, while excessive false positives create analyst workload and customer friction.

## Coefficient Interpretation

`outputs/fraud_model_coefficients.csv` records the transformed feature name, signed coefficient, absolute coefficient, direction, and rank. Positive coefficients increase model log-odds; negative coefficients reduce them, holding other transformed inputs constant. They are global associations, not causal explanations. Full explainability remains Milestone 8.

## Synthetic-Data Limitations

The generated labels are synthetic and largely independent of the engineered behaviour signals. Weak discrimination is therefore expected and is useful evidence that a technically correct pipeline should not manufacture performance. Results do not represent real fraud prevalence, typologies, customer behaviour, control effectiveness, or production readiness.

## Run Locally

```bash
python3 scripts/train_fraud_baseline.py
```

The command requires no Azure credentials and writes the fitted pipeline, metadata, predictions, threshold analysis, metrics, feature list, coefficients, and Markdown report locally.

## Azure Conceptual Mapping

| Local capability | Azure-aligned concept |
| --- | --- |
| Training pipeline and metadata | Azure Machine Learning jobs, experiments, model registry, and managed endpoints |
| Feature and prediction files | Azure Data Lake Storage curated zones |
| Model-ready transaction table | Azure Synapse Analytics analytical dataset |
| Run metadata and metrics | MLflow or Azure ML experiment tracking |
| Future model telemetry | Azure Monitor and Application Insights |
| Feature and model lineage | Microsoft Purview governance |
| Fraud performance exports | Power BI operational reporting |

These are conceptual mappings only; no cloud resources or credentials are used.
