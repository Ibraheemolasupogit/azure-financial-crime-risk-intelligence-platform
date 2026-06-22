# AML Rule Engine

Milestone 6 adds a deterministic transaction-monitoring rule engine that complements the fraud baseline. Fraud prediction estimates a supervised transaction outcome; AML monitoring identifies explainable patterns that may warrant investigation across transactions, accounts, customers, devices, geography, and due-diligence indicators.

An alert is an analytical review candidate. It does not prove criminal activity, automate a legal conclusion, create a suspicious activity report, or replace investigator judgement.

## Implemented Rules

| Rule | Monitoring pattern |
| --- | --- |
| AML001 | Transaction amount above an illustrative high-value threshold |
| AML002 | Multiple sub-threshold transactions whose rolling aggregate exceeds configured limits |
| AML003 | Material transactions occurring rapidly after prior activity, including channel or country changes |
| AML004 | Synthetic configured geography matches or unexpected customer, merchant, and IP mismatches |
| AML005 | Elevated rolling cross-border frequency or ratio relative to prior customer behaviour |
| AML006 | Material account activity after a configured period of inactivity |
| AML007 | Repeated declined or reversed transactions in a rolling window |
| AML008 | Risky sessions, new devices, authentication failures, or unusual IP geography |
| AML009 | Synthetic KYC, PEP, sanctions-screening, or existing watchlist indicators |
| AML010 | Configured merchant/channel categories or jointly novel merchant and channel behaviour |

The country list is synthetic and illustrative. It does not describe any country or population as inherently criminal.

## Temporal Logic

Transactions are sorted chronologically using transaction ID as a stable tie-breaker. Structuring, cross-border, failed-transaction, rapid-movement, dormancy, and merchant/channel rules update their history only after evaluating the current transaction. No future transaction is visible to a current rule decision.

## Evidence And Determinism

Every alert contains a rule ID and name, configured severity, configured risk points, human-readable reason, and canonical JSON evidence with observed values and thresholds. Alert IDs are derived deterministically from the rule ID and transaction ID. The configured reference timestamp makes alert production reproducible for identical data and configuration.

Risk points are additive triage weights, not probabilities. They are read directly from `configs/aml_rules_config.yaml` and remain traceable in the rule summary.

## Customer Aggregation

Transaction alerts are aggregated by synthetic customer ID into rule counts, severity counts, total points, geography/device/KYC alert groups, alert chronology, and a recommended priority of `routine`, `standard`, `enhanced`, or `urgent`.

Priority is a transparent analytical triage aid. It is not customer composite risk scoring, an automated account action, or a legal or regulatory decision. Composite customer risk scoring remains a later milestone.

## Outputs

- `outputs/aml_transaction_alerts.csv`: transaction-rule alerts and evidence JSON
- `outputs/aml_customer_summary.csv`: customer-level alert exposure and triage priority
- `outputs/aml_rule_summary.csv`: configuration and coverage by rule
- `outputs/aml_run_summary.json`: machine-readable run metrics and top synthetic customer identifiers
- `reports/aml_rule_engine_report.md`: human-readable monitoring report

Run locally:

```bash
python3 scripts/run_aml_rules.py
```

The CLI loads data through the ingestion layer, runs the existing validation gate, uses selected processed transaction signals, evaluates enabled rules, and writes all outputs without Azure credentials.

## Limitations And Governance

Rule-based monitoring is explainable but can be brittle, duplicative, and prone to false positives. Broad geography, device, cross-border, and merchant conditions can create substantial alert volume. Thresholds require validation against investigation capacity, risk appetite, product context, and known legitimate behaviour.

Real implementation would also require documented control ownership, change approval, versioning, data lineage, access controls, quality monitoring, scenario validation, outcome feedback, fairness review, record retention, and independent model or control challenge. This project claims no regulatory certification or formal compliance.

## Azure Conceptual Mapping

| Local capability | Azure-aligned concept |
| --- | --- |
| Transaction events | Azure Event Hubs ingestion |
| Real-time rule functions | Azure Stream Analytics or Azure Functions |
| Transactions, alerts, and evidence | Azure Data Lake Storage |
| Rolling historical pattern analysis | Azure Synapse Analytics |
| Complementary anomaly and risk models | Azure Machine Learning |
| Later investigation assistance | Azure AI Foundry |
| Lineage and control classification | Microsoft Purview |
| Rule execution telemetry | Azure Monitor and Application Insights |
| Alert and risk dashboards | Power BI |

These mappings are conceptual only. No cloud resources, paid services, or credentials are used.
