# Monitoring Dashboard Specification

| Page | Audience | KPIs and visuals | Filters and drill-through | Alerts and sources |
| --- | --- | --- | --- | --- |
| Executive Control Health | Executives, control owners | Overall status, control counts, domain heatmap, alert trend | Domain, severity, period; drill to control | Conditional red/amber/green indicators; platform summary and alerts |
| Data Quality | Data engineering, governance | Rows, missing rates, duplicates, schema and freshness cards | Dataset, metric, status; drill to evidence | Schema and critical quality flags; data-quality monitoring |
| Feature Drift | Data science, model risk | PSI bars, TVD bars, mean-shift table, top drift ranking | Feature, category, period; drill to distributions | Threshold formatting; numeric and categorical drift outputs |
| Fraud Model Performance | Fraud analytics, model risk | Precision, recall, AP, FPR, score distribution, confusion matrix | Period, threshold, outcome; drill to predictions | Degradation warnings; fraud monitoring and predictions |
| AML Rule Operations | AML operations | Alert coverage, customer saturation, rule volumes, severity, concentration | Rule, severity, customer; drill to alerts | High-volume and zero-rule flags; AML monitoring and alerts |
| Customer Risk Distribution | Investigations, risk governance | Score histogram, bands, priorities, component averages | Band, priority, component; drill to customer ID | Concentration and reconstruction flags; risk monitoring and scores |
| Explainability Quality | Model risk, investigators | Pass rate, reconstruction differences, reason-code violations | Model version, outcome; drill to explanation | Critical integrity flags; explainability monitoring |
| GenAI Safety and Grounding | Responsible AI, compliance | Grounding/safety failures, unsupported claims, network status | Case, violation type; drill to case evidence | Critical network and content flags; GenAI monitoring and quality |
| Pipeline Health | Platform operations | Stage availability, freshness, size, parseability, status timeline | Stage, artifact, status; drill to path | Missing/stale artifact indicators; pipeline health |

All pages should use accessible conditional formatting, persistent synthetic-data labels, human-review messaging, and export controls. The future Power BI model should use the generated CSV and JSON artifacts; no `.pbix` file is created in Milestone 10.
