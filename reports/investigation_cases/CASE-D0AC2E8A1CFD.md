# Investigation Case CASE-D0AC2E8A1CFD

- Synthetic customer: `CUST-000042`
- Review priority: `enhanced`
- Risk score and band: 67.9438 (high)
- Generation mode: `deterministic_template`
- Generated timestamp: `2026-01-01T00:00:00`

## Case Overview

Observed facts: synthetic customer CUST-000042 has 137 AML alerts across 6 rules (AML002, AML004, AML005, AML008, AML009, AML010); the maximum available fraud probability is 0.7124. Analytical indicators: the configured customer risk score is 67.9438 in the high band with enhanced review priority. Recommended review actions: a human investigator should verify transaction context, review KYC and device history, examine related alerts, and document a disposition. Analytical draft requiring human review. All data and indicators are synthetic.

## Observed Transaction Indicators

- `TXN-000001184` at `2025-07-02T18:48:15`: 4 sub-threshold transactions totalled 499.26 within 720 hours.
- `TXN-000001195` at `2025-06-17T11:38:03`: 5 sub-threshold transactions totalled 579.93 within 720 hours.
- `TXN-000001198` at `2025-06-07T10:14:12`: 6 sub-threshold transactions totalled 572.83 within 720 hours.
- `TXN-000001164` at `2025-12-27T06:01:01`: Synthetic customer due-diligence or watchlist indicators require review.
- `TXN-000001192` at `2025-12-24T18:25:44`: Synthetic customer due-diligence or watchlist indicators require review.

## AML Rules Triggered

`AML002`, `AML004`, `AML005`, `AML008`, `AML009`, `AML010`

## Fraud Model Indicators

- `TXN-000001192` probability 0.7124; explanation `passed`
- `TXN-000001164` probability 0.5522; explanation `passed`
- `TXN-000001185` probability 0.3690; explanation `passed`
- `TXN-000001162` probability 0.2120; explanation `passed`
- `TXN-000001193` probability 0.2082; explanation `passed`

## Model Explanation Factors

- Observed merchant country=SG reduced the model decision score.
- Observed ip country=ES increased the model decision score.
- Observed customer country=ES reduced the model decision score.
- Observed high risk channel flag=1 increased the model decision score.
- Observed currency=EUR reduced the model decision score.

## Evidence Table

| Evidence | Value |
| --- | --- |
| AML alerts | 137 |
| Distinct AML rules | 6 |
| Maximum fraud probability | 0.7124 |

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
