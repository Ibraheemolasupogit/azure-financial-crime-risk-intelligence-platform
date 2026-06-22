# Fraud Model Explainability Report

- Model: `1.0.0-baseline` (LogisticRegression)
- Transactions explained: 367
- Transformed features: 88
- Source features: 34
- Explanation quality: `passed`
- Passed / failed: 367 / 0
- Maximum decision difference: 5.329e-15
- Maximum probability difference: 3.331e-16

## Methodology

For each transformed input, local contribution equals transformed value multiplied by its Logistic Regression coefficient. Contributions plus the intercept reconstruct the decision score; applying the logistic function reconstructs probability.

## Strongest Positive Associations

- `categorical__ip_country_IE`: 1.727286
- `categorical__ip_country_ES`: 1.400823
- `numeric__amount_vs_customer_average`: 1.096502
- `categorical__customer_country_DE`: 1.031800
- `numeric__transaction_count_customer_24h`: 1.021768
- `categorical__merchant_country_GB`: 0.789485
- `categorical__merchant_country_BR`: 0.780265
- `numeric__is_cross_border`: 0.751535
- `categorical__merchant_country_CA`: 0.719043
- `numeric__distinct_countries_customer_7d`: 0.634069

## Strongest Negative Associations

- `numeric__amount_vs_account_average`: -2.295765
- `categorical__ip_country_FR`: -1.648696
- `categorical__merchant_country_SG`: -1.483781
- `numeric__transaction_velocity_score`: -1.279600
- `categorical__ip_country_ZA`: -1.117885
- `numeric__transaction_amount_customer_24h`: -1.049156
- `categorical__merchant_country_DE`: -0.886899
- `categorical__customer_country_ES`: -0.800456
- `categorical__currency_CAD`: -0.800077
- `categorical__customer_country_CA`: -0.800077

## Common Local Reason Codes

- `FRC_CURRENCY_DOWN`: 179
- `FRC_AMOUNT_VS_ACCOUNT_AVERAGE_UP`: 158
- `FRC_IP_COUNTRY_UP`: 144
- `FRC_DISTINCT_COUNTRIES_CUSTOMER_7D_DOWN`: 137
- `FRC_IP_COUNTRY_DOWN`: 123
- `FRC_CUSTOMER_COUNTRY_DOWN`: 120
- `FRC_MERCHANT_COUNTRY_UP`: 108
- `FRC_HIGH_RISK_CHANNEL_FLAG_UP`: 106
- `FRC_DISTINCT_MERCHANTS_CUSTOMER_7D_UP`: 88
- `FRC_MERCHANT_CATEGORY_DOWN`: 87

## False Positives And Limitations

The synthetic baseline produces many false positives. Explanations show which model associations drove those scores; they do not make the predictions correct or causal.

Coefficients and local contributions describe model behaviour, not real-world causes, customer intent, fraud, or criminal conduct. Categorical levels remain encoded model terms even when aggregated to source features for readability.

Explanations require trained human interpretation, source-data review, model-version linkage, reproducibility controls, and documented challenge before any action.

All explanation inputs, labels, identifiers, and outputs are synthetic.
