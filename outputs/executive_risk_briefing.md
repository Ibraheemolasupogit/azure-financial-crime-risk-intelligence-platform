# Executive Synthetic Investigation Briefing

- Cases selected: 5
- Risk bands: {'critical': 1, 'high': 4}
- Review priorities: {'urgent': 1, 'enhanced': 4}
- High-priority synthetic identifiers: CUST-000018, CUST-000049, CUST-000010, CUST-000034, CUST-000042
- Dominant AML rules: [('AML002', 5), ('AML004', 5), ('AML005', 5), ('AML008', 5), ('AML010', 5)]
- Dominant risk components: [('aml_alert', 4), ('transaction_behaviour', 1)]

## Operational View

The selected cases combine elevated configured customer-risk scores, AML alert exposure, and fraud-model indicators. The fraud baseline has weak synthetic discrimination and a substantial false-positive burden, so model scores require careful contextual review.

Key operational risks include broad AML thresholds, correlated indicators, duplicate investigation workload, data-quality dependency, and overreliance on generated drafts.

Recommended controls: review scenario thresholds and score weights, assess false-positive capacity, verify evidence lineage, and require documented human disposition.

Analytical draft requiring human review. All data and indicators are synthetic.
