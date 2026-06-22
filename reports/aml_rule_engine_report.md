# AML Rule Engine Report

- Run timestamp: `2026-06-22T20:11:28+00:00`
- Overall status: `passed`
- Transactions evaluated: 1468
- Enabled rules: 10
- Total alerts: 3549
- Alerted transactions: 1405
- Affected customers: 50

## Rule Results

| Rule | Name | Severity | Alerts | Customers | Transaction coverage |
| --- | --- | --- | ---: | ---: | ---: |
| AML001 | High-value transaction | high | 28 | 24 | 1.91% |
| AML002 | Structuring or smurfing | high | 250 | 37 | 17.03% |
| AML003 | Rapid movement of funds | high | 17 | 12 | 1.16% |
| AML004 | High-risk geography | medium | 474 | 49 | 32.29% |
| AML005 | Unusual cross-border activity | medium | 773 | 48 | 52.66% |
| AML006 | Dormant or low-activity account reactivation | high | 8 | 8 | 0.55% |
| AML007 | Repeated failed transactions | medium | 12 | 10 | 0.82% |
| AML008 | Device or session risk | medium | 767 | 50 | 52.25% |
| AML009 | KYC, PEP, sanctions, or watchlist exposure | high | 286 | 11 | 19.48% |
| AML010 | Unusual merchant or channel pattern | low | 934 | 50 | 63.62% |

## Alerts By Severity

- high: 589
- low: 934
- medium: 2026

## Highest-Risk Synthetic Customers

- `CUST-000010`: 156 alerts, 3131 points, urgent priority
- `CUST-000018`: 148 alerts, 3097 points, urgent priority
- `CUST-000042`: 137 alerts, 2923 points, urgent priority
- `CUST-000034`: 144 alerts, 2799 points, urgent priority
- `CUST-000049`: 132 alerts, 2571 points, urgent priority

## Interpretation

Each alert identifies the rule, observed values, configured conditions, severity, and traceable risk points. Alerts indicate analytical review candidates only; they do not prove criminal activity or automate a legal or regulatory conclusion.

The configured country list is synthetic and illustrative. It does not classify any country or population as inherently criminal.
