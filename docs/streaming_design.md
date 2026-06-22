# Streaming Design

## Local-to-Azure Mapping

The local `transactions.jsonl` file is a replayable stand-in for immutable transaction events. In Azure, producers publish versioned envelopes to Event Hubs. A stable `account_id` partition key preserves account-relative order while distributing load; hot-account analysis must validate partition skew.

Separate consumer groups isolate validation, low-latency fraud scoring, AML evaluation, lake capture, and observability. Consumers checkpoint only after durable processing. Event Hubs retention and Capture support replay into ADLS; replay jobs preserve original event IDs and processing versions.

## Delivery Controls

- Idempotency: deduplicate on `event_id` plus processing-version at durable sinks.
- Schema evolution: version envelopes, reject incompatible changes, and use backward-compatible additive fields.
- Dead-letter handling: route invalid or repeatedly failing events to a restricted quarantine store with reason, payload hash, and correlation ID.
- Checkpointing: use partition-aware checkpoints and monitor lag, failure count, and checkpoint age.
- Replay: use isolated consumer groups and explicit time ranges; prevent duplicate alerts through idempotent output keys.

## Processing Options

Stream Analytics suits declarative windows, velocity features, routing, and aggregations. Functions suit custom validation, orchestration, and endpoint invocation. A low-latency path validates the event, constructs approved online features, calls a private AAD-authenticated Azure ML endpoint, applies response timeouts, records model/version/feature lineage, and routes predictions for AML and customer-risk context.

AML rules may execute in Stream Analytics for windowed scenarios or Functions/jobs for richer state. Alert routing should use durable queues or case APIs with human review, not autonomous legal conclusions. Telemetry flows to Application Insights and Log Analytics. The sample SQL and function are illustrative and make no calls.
