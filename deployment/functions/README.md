# Azure Functions Mapping

`function_app_placeholder.py` demonstrates only local event validation. It makes no network calls and is not an Azure Function deployment package.

In an approved Azure design, Functions could validate schemas, enrich events, invoke an authenticated private Azure ML endpoint, evaluate lightweight AML controls, and route evidence. Production controls would include Event Hubs triggers, managed identity, private networking, idempotency storage, poison-event routing, retries with bounded backoff, distributed tracing, structured logs, deployment slots, and load tests. Connection strings and secrets must not be embedded.
