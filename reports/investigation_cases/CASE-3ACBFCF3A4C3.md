# Investigation Case CASE-3ACBFCF3A4C3

- Synthetic customer: `CUST-000049`
- Review priority: `enhanced`
- Risk score and band: 70.2650 (high)
- Generation mode: `deterministic_template`
- Generated timestamp: `2026-01-01T00:00:00`

## Case Overview

Observed facts: synthetic customer CUST-000049 has 132 AML alerts across 9 rules (AML001, AML002, AML003, AML004, AML005, AML006, AML007, AML008, AML010); the maximum available fraud probability is 0.9275. Analytical indicators: the configured customer risk score is 70.2650 in the high band with enhanced review priority. Recommended review actions: a human investigator should verify transaction context, review KYC and device history, examine related alerts, and document a disposition. Analytical draft requiring human review. All data and indicators are synthetic.

## Observed Transaction Indicators

- `TXN-000001411` at `2025-11-14T21:39:46`: 6 sub-threshold transactions totalled 316.83 within 720 hours.
- `TXN-000001408` at `2025-11-06T18:16:56`: 7 sub-threshold transactions totalled 648.16 within 720 hours.
- `TXN-000001449` at `2025-10-28T08:48:05`: 10 sub-threshold transactions totalled 799.53 within 720 hours.
- `TXN-000001402` at `2025-10-20T14:12:16`: 10 sub-threshold transactions totalled 795.23 within 720 hours.
- `TXN-000001438` at `2025-10-17T06:10:17`: 10 sub-threshold transactions totalled 847.44 within 720 hours.

## AML Rules Triggered

`AML001`, `AML002`, `AML003`, `AML004`, `AML005`, `AML006`, `AML007`, `AML008`, `AML010`

## Fraud Model Indicators

- `TXN-000001438` probability 0.9275; explanation `passed`
- `TXN-000001437` probability 0.8043; explanation `passed`
- `TXN-000001451` probability 0.8024; explanation `passed`
- `TXN-000001409` probability 0.7899; explanation `passed`
- `TXN-000001428` probability 0.6648; explanation `passed`

## Model Explanation Factors

- Observed customer country=IE reduced the model decision score.
- Observed ip country=IE increased the model decision score.
- Observed currency=EUR reduced the model decision score.
- Observed merchant country=GB increased the model decision score.
- Observed distinct countries customer 7d=0 reduced the model decision score.

## Evidence Table

| Evidence | Value |
| --- | --- |
| AML alerts | 132 |
| Distinct AML rules | 9 |
| Maximum fraud probability | 0.9275 |

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
