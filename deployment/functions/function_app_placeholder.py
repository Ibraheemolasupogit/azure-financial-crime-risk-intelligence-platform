"""Non-networking placeholder for an event validation function.

This module intentionally imports no Azure SDK and invokes no external endpoint.
"""

from typing import Any

REQUIRED_FIELDS = {"schema_version", "event_id", "event_type", "occurred_at", "transaction"}


def validate_transaction_event(event: dict[str, Any]) -> dict[str, Any]:
    """Return a local validation result suitable for unit-level design discussion."""
    missing = sorted(REQUIRED_FIELDS.difference(event))
    transaction = event.get("transaction", {})
    amount = transaction.get("amount") if isinstance(transaction, dict) else None
    errors = [f"missing field: {field}" for field in missing]
    if amount is None or not isinstance(amount, (int, float)) or amount <= 0:
        errors.append("transaction.amount must be a positive number")
    return {
        "event_id": event.get("event_id"),
        "is_valid": not errors,
        "errors": errors,
        "network_call_made": False,
    }
