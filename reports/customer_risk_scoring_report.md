# Customer Risk Scoring Report

- Run timestamp: `2026-06-22T20:23:58+00:00`
- Score version: `1.0.0`
- Customers scored: 50
- Average score: 47.9562
- Median score: 45.8022
- Score range: 21.7171 to 78.1571
- Dominant average component: `transaction_behaviour`
- Weights reconstruct totals: `True`

## Methodology

Each component is capped and normalised to 0-100. The total is the sum of rounded weighted contributions:

`total = 0.20 x KYC + 0.20 x transaction + 0.30 x AML + 0.15 x fraud model + 0.15 x device/session`

## Risk Distribution

- moderate: 32
- high: 14
- low: 3
- critical: 1

## Review Priorities

- standard: 29
- enhanced: 19
- urgent: 1
- routine: 1

## Average Component Scores

- aml_alert: 49.3124
- device_session: 56.0333
- fraud_model: 55.4918
- kyc: 10.6000
- transaction_behaviour: 71.5686

## Highest-Risk Synthetic Identifiers

- `CUST-000018`: 78.1571, critical; 43 high/critical AML alerts; 3 structuring alerts; 148 total AML alerts
- `CUST-000049`: 70.2650, high; 23 high/critical AML alerts; 19 structuring alerts; 132 total AML alerts
- `CUST-000010`: 69.8056, high; 30 high/critical AML alerts; 27 structuring alerts; 156 total AML alerts
- `CUST-000034`: 68.3014, high; 24 high/critical AML alerts; 21 structuring alerts; 144 total AML alerts
- `CUST-000042`: 67.9438, high; 45 high/critical AML alerts; 3 structuring alerts; 137 total AML alerts

## Governance And Limitations

Risk bands are analytical categories and priorities are investigation triage aids. Neither independently justifies adverse action or a legal or regulatory decision.

Actual fraud labels are excluded from scoring and used only in a separately written retrospective evaluation. Synthetic labels have weak behavioural signal.

Weights, caps, and thresholds require formal approval, monitoring, fairness review, data-quality controls, and tuning against investigation capacity before real use.
