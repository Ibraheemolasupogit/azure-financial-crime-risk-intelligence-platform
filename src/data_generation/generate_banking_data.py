"""Generate deterministic synthetic banking datasets for local development."""

from __future__ import annotations

import csv
import json
import random
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

CUSTOMER_FIELDS = [
    "customer_id",
    "first_name",
    "last_name",
    "date_of_birth",
    "age_band",
    "country",
    "customer_segment",
    "employment_status",
    "annual_income_band",
    "onboarding_date",
    "kyc_status",
    "pep_flag",
    "sanctions_screening_status",
    "customer_risk_rating",
]

ACCOUNT_FIELDS = [
    "account_id",
    "customer_id",
    "account_type",
    "account_open_date",
    "account_status",
    "currency",
    "branch_region",
    "average_monthly_balance_band",
]

TRANSACTION_FIELDS = [
    "transaction_id",
    "account_id",
    "customer_id",
    "transaction_timestamp",
    "transaction_type",
    "channel",
    "merchant_category",
    "merchant_country",
    "amount",
    "currency",
    "is_cross_border",
    "transaction_status",
    "device_id",
    "session_id",
]

SESSION_FIELDS = [
    "session_id",
    "customer_id",
    "device_id",
    "session_timestamp",
    "ip_country",
    "device_type",
    "operating_system",
    "login_success",
    "authentication_method",
    "session_risk_signal",
]

FRAUD_LABEL_FIELDS = [
    "transaction_id",
    "fraud_label",
    "fraud_typology",
    "label_confidence",
    "label_source",
]

AML_WATCHLIST_FIELDS = [
    "watchlist_id",
    "customer_id",
    "watchlist_type",
    "alert_reason",
    "alert_severity",
    "created_date",
    "review_status",
]

COUNTRIES = ["GB", "IE", "FR", "DE", "ES", "NL", "US", "CA", "SG", "AE"]
MERCHANT_COUNTRIES = COUNTRIES + ["TR", "ZA", "BR"]
CURRENCIES_BY_COUNTRY = {
    "GB": "GBP",
    "IE": "EUR",
    "FR": "EUR",
    "DE": "EUR",
    "ES": "EUR",
    "NL": "EUR",
    "US": "USD",
    "CA": "CAD",
    "SG": "SGD",
    "AE": "AED",
}


def _weighted_choice(rng: random.Random, choices: list[tuple[str, float]]) -> str:
    labels, weights = zip(*choices, strict=True)
    return rng.choices(labels, weights=weights, k=1)[0]


def _random_date(rng: random.Random, start: date, end: date) -> date:
    days = (end - start).days
    return start + timedelta(days=rng.randint(0, days))


def _age_band(age: int) -> str:
    if age < 25:
        return "18-24"
    if age < 35:
        return "25-34"
    if age < 45:
        return "35-44"
    if age < 55:
        return "45-54"
    if age < 65:
        return "55-64"
    return "65+"


def generate_customers(number_of_customers: int, rng: random.Random) -> list[dict[str, Any]]:
    """Generate synthetic customer profile records."""
    customers: list[dict[str, Any]] = []
    today = date(2026, 1, 1)

    for index in range(1, number_of_customers + 1):
        age = rng.randint(18, 78)
        dob = today.replace(year=today.year - age) - timedelta(days=rng.randint(0, 364))
        country = rng.choice(COUNTRIES)
        risk_rating = _weighted_choice(rng, [("Low", 0.66), ("Medium", 0.27), ("High", 0.07)])
        pep_flag = risk_rating == "High" and rng.random() < 0.25

        customers.append(
            {
                "customer_id": f"CUST-{index:06d}",
                "first_name": f"SyntheticFirst{index:06d}",
                "last_name": f"SyntheticLast{index:06d}",
                "date_of_birth": dob.isoformat(),
                "age_band": _age_band(age),
                "country": country,
                "customer_segment": rng.choice(["Retail", "Premier", "SME", "Student"]),
                "employment_status": rng.choice(
                    ["Employed", "Self-employed", "Student", "Retired", "Unemployed"]
                ),
                "annual_income_band": rng.choice(
                    ["0-25k", "25k-50k", "50k-100k", "100k-250k", "250k+"]
                ),
                "onboarding_date": _random_date(
                    rng, date(2018, 1, 1), date(2025, 12, 31)
                ).isoformat(),
                "kyc_status": _weighted_choice(
                    rng,
                    [
                        ("Verified", 0.9),
                        ("Pending Review", 0.07),
                        ("Enhanced Due Diligence", 0.03),
                    ],
                ),
                "pep_flag": pep_flag,
                "sanctions_screening_status": _weighted_choice(
                    rng, [("Clear", 0.94), ("Potential Match", 0.05), ("Escalated", 0.01)]
                ),
                "customer_risk_rating": risk_rating,
            }
        )

    return customers


def generate_accounts(
    customers: list[dict[str, Any]],
    accounts_per_customer_min: int,
    accounts_per_customer_max: int,
    rng: random.Random,
) -> list[dict[str, Any]]:
    """Generate synthetic accounts linked to customers."""
    accounts: list[dict[str, Any]] = []
    account_index = 1

    for customer in customers:
        account_count = rng.randint(accounts_per_customer_min, accounts_per_customer_max)
        customer_currency = CURRENCIES_BY_COUNTRY.get(str(customer["country"]), "GBP")

        for _ in range(account_count):
            accounts.append(
                {
                    "account_id": f"ACC-{account_index:07d}",
                    "customer_id": customer["customer_id"],
                    "account_type": rng.choice(["Current", "Savings", "Credit", "Business"]),
                    "account_open_date": _random_date(
                        rng, date.fromisoformat(str(customer["onboarding_date"])), date(2026, 1, 1)
                    ).isoformat(),
                    "account_status": _weighted_choice(
                        rng, [("Active", 0.92), ("Dormant", 0.05), ("Restricted", 0.03)]
                    ),
                    "currency": customer_currency,
                    "branch_region": rng.choice(
                        ["London", "Manchester", "Birmingham", "Scotland", "Wales", "Digital"]
                    ),
                    "average_monthly_balance_band": rng.choice(
                        ["0-1k", "1k-5k", "5k-25k", "25k-100k", "100k+"]
                    ),
                }
            )
            account_index += 1

    return accounts


def generate_device_sessions(
    customers: list[dict[str, Any]], rng: random.Random, sessions_per_customer: int = 4
) -> list[dict[str, Any]]:
    """Generate synthetic digital banking sessions linked to customers."""
    sessions: list[dict[str, Any]] = []
    session_index = 1

    for customer in customers:
        home_country = str(customer["country"])
        for device_number in range(1, sessions_per_customer + 1):
            ip_country = home_country if rng.random() < 0.82 else rng.choice(MERCHANT_COUNTRIES)
            high_risk = ip_country != home_country and rng.random() < 0.35
            sessions.append(
                {
                    "session_id": f"SES-{session_index:08d}",
                    "customer_id": customer["customer_id"],
                    "device_id": f"DEV-{customer['customer_id'][-6:]}-{device_number:02d}",
                    "session_timestamp": (
                        datetime(2025, 1, 1)
                        + timedelta(
                            days=rng.randint(0, 364),
                            hours=rng.randint(0, 23),
                            minutes=rng.randint(0, 59),
                        )
                    ).isoformat(timespec="seconds"),
                    "ip_country": ip_country,
                    "device_type": rng.choice(["Mobile", "Desktop", "Tablet"]),
                    "operating_system": rng.choice(["iOS", "Android", "Windows", "macOS", "Linux"]),
                    "login_success": rng.random() > 0.04,
                    "authentication_method": rng.choice(
                        ["Password", "Biometric", "MFA Push", "One-time Passcode"]
                    ),
                    "session_risk_signal": (
                        "Elevated" if high_risk else rng.choice(["Low", "Low", "Medium"])
                    ),
                }
            )
            session_index += 1

    return sessions


def generate_transactions(
    accounts: list[dict[str, Any]],
    device_sessions: list[dict[str, Any]],
    transactions_per_account_min: int,
    transactions_per_account_max: int,
    rng: random.Random,
) -> list[dict[str, Any]]:
    """Generate synthetic transactions linked to accounts and sessions."""
    sessions_by_customer: dict[str, list[dict[str, Any]]] = {}
    for session in device_sessions:
        sessions_by_customer.setdefault(str(session["customer_id"]), []).append(session)

    transactions: list[dict[str, Any]] = []
    transaction_index = 1

    for account in accounts:
        transaction_count = rng.randint(transactions_per_account_min, transactions_per_account_max)
        customer_id = str(account["customer_id"])
        customer_sessions = sessions_by_customer[customer_id]

        for _ in range(transaction_count):
            session = rng.choice(customer_sessions)
            merchant_country = rng.choice(MERCHANT_COUNTRIES)
            amount = round(rng.lognormvariate(3.3, 1.0), 2)
            if rng.random() < 0.03:
                amount = round(amount * rng.uniform(8, 30), 2)

            transactions.append(
                {
                    "transaction_id": f"TXN-{transaction_index:09d}",
                    "account_id": account["account_id"],
                    "customer_id": customer_id,
                    "transaction_timestamp": (
                        datetime(2025, 1, 1)
                        + timedelta(
                            days=rng.randint(0, 364),
                            hours=rng.randint(0, 23),
                            minutes=rng.randint(0, 59),
                            seconds=rng.randint(0, 59),
                        )
                    ).isoformat(timespec="seconds"),
                    "transaction_type": rng.choice(
                        ["Card Purchase", "Bank Transfer", "Cash Withdrawal", "Direct Debit"]
                    ),
                    "channel": rng.choice(["Mobile App", "Online Banking", "ATM", "Branch", "POS"]),
                    "merchant_category": rng.choice(
                        [
                            "Grocery",
                            "Travel",
                            "Electronics",
                            "Entertainment",
                            "Crypto Exchange",
                            "Money Transfer",
                            "Cash Services",
                            "Utilities",
                        ]
                    ),
                    "merchant_country": merchant_country,
                    "amount": amount,
                    "currency": account["currency"],
                    "is_cross_border": merchant_country != session["ip_country"],
                    "transaction_status": _weighted_choice(
                        rng, [("Approved", 0.94), ("Declined", 0.04), ("Reversed", 0.02)]
                    ),
                    "device_id": session["device_id"],
                    "session_id": session["session_id"],
                }
            )
            transaction_index += 1

    return transactions


def generate_fraud_labels(
    transactions: list[dict[str, Any]], fraud_rate: float, rng: random.Random
) -> list[dict[str, Any]]:
    """Generate synthetic fraud labels referencing transaction IDs."""
    labels: list[dict[str, Any]] = []
    typologies = [
        "Account Takeover",
        "Card Not Present Fraud",
        "Synthetic Identity Pattern",
        "Mule Account Activity",
        "Unauthorized Transfer",
    ]

    for transaction in transactions:
        fraud_label = rng.random() < fraud_rate
        labels.append(
            {
                "transaction_id": transaction["transaction_id"],
                "fraud_label": int(fraud_label),
                "fraud_typology": rng.choice(typologies) if fraud_label else "Not Fraud",
                "label_confidence": round(
                    rng.uniform(0.72, 0.99) if fraud_label else rng.uniform(0.85, 1),
                    3,
                ),
                "label_source": rng.choice(
                    ["Synthetic Rule", "Synthetic Analyst Review", "Synthetic Model"]
                ),
            }
        )

    return labels


def generate_aml_watchlist(
    customers: list[dict[str, Any]], aml_watchlist_rate: float, rng: random.Random
) -> list[dict[str, Any]]:
    """Generate synthetic AML watchlist alerts referencing customer IDs."""
    watchlist: list[dict[str, Any]] = []
    alert_index = 1

    for customer in customers:
        risk_rating = str(customer["customer_risk_rating"])
        probability = aml_watchlist_rate + (0.1 if risk_rating == "High" else 0)
        if rng.random() <= probability:
            severity = "High" if risk_rating == "High" else rng.choice(["Low", "Medium"])
            watchlist.append(
                {
                    "watchlist_id": f"AML-{alert_index:07d}",
                    "customer_id": customer["customer_id"],
                    "watchlist_type": rng.choice(
                        [
                            "PEP Review",
                            "Sanctions Screening",
                            "Adverse Media",
                            "Transaction Pattern",
                        ]
                    ),
                    "alert_reason": rng.choice(
                        [
                            "Synthetic risk factor threshold exceeded",
                            "Synthetic cross-border activity pattern",
                            "Synthetic enhanced due diligence trigger",
                            "Synthetic adverse media simulation",
                        ]
                    ),
                    "alert_severity": severity,
                    "created_date": _random_date(
                        rng, date(2025, 1, 1), date(2025, 12, 31)
                    ).isoformat(),
                    "review_status": rng.choice(
                        ["Open", "In Review", "Closed - No Issue", "Escalated"]
                    ),
                }
            )
            alert_index += 1

    if not watchlist and customers:
        customer = rng.choice(customers)
        watchlist.append(
            {
                "watchlist_id": "AML-0000001",
                "customer_id": customer["customer_id"],
                "watchlist_type": "Transaction Pattern",
                "alert_reason": "Synthetic minimum sample alert",
                "alert_severity": "Low",
                "created_date": date(2025, 1, 1).isoformat(),
                "review_status": "Open",
            }
        )

    return watchlist


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    """Write rows to CSV with a stable header."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    """Write rows to newline-delimited JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, sort_keys=True))
            file.write("\n")


def generate_all_datasets(config: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Generate all Milestone 2 datasets from a configuration dictionary."""
    rng = random.Random(int(config["random_seed"]))
    customers = generate_customers(int(config["number_of_customers"]), rng)
    accounts = generate_accounts(
        customers,
        int(config["accounts_per_customer_min"]),
        int(config["accounts_per_customer_max"]),
        rng,
    )
    sessions = generate_device_sessions(customers, rng)
    transactions = generate_transactions(
        accounts,
        sessions,
        int(config["transactions_per_account_min"]),
        int(config["transactions_per_account_max"]),
        rng,
    )
    fraud_labels = generate_fraud_labels(transactions, float(config["fraud_rate"]), rng)
    aml_watchlist = generate_aml_watchlist(customers, float(config["aml_watchlist_rate"]), rng)

    return {
        "customers": customers,
        "accounts": accounts,
        "transactions": transactions,
        "device_sessions": sessions,
        "fraud_labels": fraud_labels,
        "aml_watchlist": aml_watchlist,
    }


def write_all_datasets(
    output_dir: Path, datasets: dict[str, list[dict[str, Any]]]
) -> dict[str, Path]:
    """Write all datasets to the configured output directory."""
    output_paths = {
        "customers": output_dir / "customers.csv",
        "accounts": output_dir / "accounts.csv",
        "transactions": output_dir / "transactions.jsonl",
        "device_sessions": output_dir / "device_sessions.jsonl",
        "fraud_labels": output_dir / "fraud_labels.csv",
        "aml_watchlist": output_dir / "aml_watchlist.csv",
    }

    write_csv(output_paths["customers"], datasets["customers"], CUSTOMER_FIELDS)
    write_csv(output_paths["accounts"], datasets["accounts"], ACCOUNT_FIELDS)
    write_jsonl(output_paths["transactions"], datasets["transactions"])
    write_jsonl(output_paths["device_sessions"], datasets["device_sessions"])
    write_csv(output_paths["fraud_labels"], datasets["fraud_labels"], FRAUD_LABEL_FIELDS)
    write_csv(output_paths["aml_watchlist"], datasets["aml_watchlist"], AML_WATCHLIST_FIELDS)

    return output_paths
