-- Illustrative Azure Stream Analytics query; not executed by this repository.
-- Durable idempotency and model invocation belong in an approved downstream service.
WITH ValidTransactions AS (
    SELECT
        event_id,
        transaction.transaction_id AS transaction_id,
        transaction.account_id AS account_id,
        transaction.customer_id AS customer_id,
        CAST(transaction.amount AS float) AS amount,
        transaction.currency AS currency,
        transaction.channel AS channel,
        System.Timestamp() AS processed_at
    FROM transactionInput TIMESTAMP BY occurred_at
    WHERE schema_version = '1.0' AND transaction.amount > 0
)
SELECT * INTO validatedTransactionOutput FROM ValidTransactions;

SELECT
    account_id,
    COUNT(*) AS transaction_count_5m,
    SUM(amount) AS transaction_amount_5m,
    System.Timestamp() AS window_end
INTO velocityFeatureOutput
FROM ValidTransactions
GROUP BY account_id, HoppingWindow(minute, 5, 1);
