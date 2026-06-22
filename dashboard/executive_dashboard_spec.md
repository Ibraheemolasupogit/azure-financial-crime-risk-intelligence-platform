# Executive Dashboard Specification

| Page | Audience and purpose | Visuals | Filters, drill-through, tooltips, formatting, accessibility |
| --- | --- | --- | --- |
| Executive Overview | Executives and control owners; portfolio health | KPI cards, transaction trend, risk bands, AML severity, monitoring status | Date/country filters; drill to domain pages; definition tooltips; status colours plus icons; keyboard and contrast support |
| Fraud Analytics | Fraud teams and model risk; performance and workload | Probability histogram, confusion matrix, precision/recall, FP trend, channel/category bars, reason-code ranking | Date/channel/category/outcome slicers; transaction explanation drill-through; metric caveats in tooltips |
| AML Operations | AML operations; rule volume and concentration | Alerts by rule/severity, alerted rate, customer coverage, concentration, high-alert customers | Rule/severity/date slicers; customer and alert drill-through; warning thresholds highlighted |
| Customer Risk | Investigators and governance; score distribution | Histogram, bands, priorities, component comparison, driver ranking | Band/priority/component slicers; customer drill-through; human-review tooltip |
| Investigation Cases | Investigation management; synthetic case queue | Queue table, priorities, drivers, AML/fraud evidence, safety status | Priority/band/status filters; case drill-through; grounding tooltip; visible human-review flag |
| Model Explainability | Investigators and model risk; model behaviour | Global associations, reason codes, error-type matrix, quality cards | Outcome/feature/direction filters; transaction drill-through; non-causal caveats |
| Platform Monitoring | Platform and control teams; operational health | Status cards, warnings, PSI/TVD, model metrics, AML workload, pipeline freshness | Domain/status/date filters; control drill-through; accessible traffic-light symbols |

Every page must display a synthetic-data banner, avoid personal details, use descriptive alt text, support tab order, avoid colour-only meaning, and expose KPI definitions through tooltips.
