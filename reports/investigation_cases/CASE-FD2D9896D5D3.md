# Investigation Case CASE-FD2D9896D5D3

- Synthetic customer: `CUST-000018`
- Review priority: `urgent`
- Risk score and band: 78.1571 (critical)
- Generation mode: `deterministic_template`
- Generated timestamp: `2026-01-01T00:00:00`

## Case Overview

Observed facts: synthetic customer CUST-000018 has 148 AML alerts across 7 rules (AML001, AML002, AML004, AML005, AML008, AML009, AML010); the maximum available fraud probability is 0.6272. Analytical indicators: the configured customer risk score is 78.1571 in the critical band with urgent review priority. Recommended review actions: a human investigator should verify transaction context, review KYC and device history, examine related alerts, and document a disposition. Analytical draft requiring human review. All data and indicators are synthetic.

## Observed Transaction Indicators

- `TXN-000000420` at `2025-12-23T00:07:29`: 6 sub-threshold transactions totalled 394.49 within 720 hours.
- `TXN-000000403` at `2025-12-22T06:29:30`: 5 sub-threshold transactions totalled 378.56 within 720 hours.
- `TXN-000000418` at `2025-06-12T21:21:40`: 6 sub-threshold transactions totalled 360.77 within 720 hours.
- `TXN-000000420` at `2025-12-23T00:07:29`: Synthetic customer due-diligence or watchlist indicators require review.
- `TXN-000000403` at `2025-12-22T06:29:30`: Synthetic customer due-diligence or watchlist indicators require review.

## AML Rules Triggered

`AML001`, `AML002`, `AML004`, `AML005`, `AML008`, `AML009`, `AML010`

## Fraud Model Indicators

- `TXN-000000407` probability 0.6272; explanation `passed`
- `TXN-000000405` probability 0.6000; explanation `passed`
- `TXN-000000412` probability 0.5718; explanation `passed`
- `TXN-000000403` probability 0.3568; explanation `passed`
- `TXN-000000427` probability 0.2874; explanation `passed`

## Model Explanation Factors

- Observed currency=CAD reduced the model decision score.
- Observed ip country=CA increased the model decision score.
- Observed customer country=CA reduced the model decision score.
- Observed transaction day of week=0 increased the model decision score.
- Observed amount vs account average=3.947312915653316 reduced the model decision score.

## Evidence Table

| Evidence | Value |
| --- | --- |
| AML alerts | 148 |
| Distinct AML rules | 7 |
| Maximum fraud probability | 0.6272 |

## Key Uncertainties And Possible Benign Explanations

- Structured indicators do not establish intent or wrongdoing.
- Travel, legitimate international activity, new devices, or expected customer behaviour may explain signals.
- Data quality, model error, and broad rule thresholds may contribute false positives.

## Recommended Investigator Checks

- Verify source and destination context.
- Review customer transaction history and KYC status.
- Review device and authentication history.
- Examine related alerts and document investigator disposition.

## Limitations

This is a deterministic analytical draft based only on supplied structured evidence.

Analytical draft requiring human review. All data and indicators are synthetic.
