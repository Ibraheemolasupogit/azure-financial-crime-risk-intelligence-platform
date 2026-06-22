#!/usr/bin/env python3
"""Perform non-deploying static validation of the illustrative Bicep scaffold."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INFRA = ROOT / "infra"

EXPECTED_FILES = [
    "main.bicep",
    "main.parameters.example.json",
    "README.md",
    "modules/resource-group-scope.bicep",
    "modules/storage.bicep",
    "modules/event-hubs.bicep",
    "modules/key-vault.bicep",
    "modules/log-analytics.bicep",
    "modules/application-insights.bicep",
    "modules/machine-learning.bicep",
    "modules/container-registry.bicep",
    "modules/synapse.bicep",
    "modules/purview-placeholder.bicep",
    "modules/networking.bicep",
    "modules/monitoring.bicep",
]
REQUIRED_PARAMETERS = {"location", "environment", "namePrefix"}
NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")
MODULE_REFERENCE_PATTERN = re.compile(r"module\s+\w+\s+'([^']+\.bicep)'", re.MULTILINE)
PARAMETER_PATTERN = re.compile(r"^param\s+(\w+)\s+", re.MULTILINE)


def validate_infrastructure(root: Path = ROOT) -> dict[str, object]:
    """Return static validation results without invoking Azure or Bicep tooling."""
    infra = root / "infra"
    checks: list[dict[str, str]] = []

    def record(name: str, passed: bool, detail: str = "") -> None:
        checks.append({"name": name, "status": "passed" if passed else "failed", "detail": detail})

    missing = [path for path in EXPECTED_FILES if not (infra / path).is_file()]
    record("expected_files", not missing, ", ".join(missing))

    main_path = infra / "main.bicep"
    main_text = main_path.read_text(encoding="utf-8") if main_path.exists() else ""
    declared = set(PARAMETER_PATTERN.findall(main_text))
    missing_parameters = sorted(REQUIRED_PARAMETERS - declared)
    record("required_parameters", not missing_parameters, ", ".join(missing_parameters))

    unresolved: list[str] = []
    for reference in MODULE_REFERENCE_PATTERN.findall(main_text):
        if not (infra / reference).is_file():
            unresolved.append(reference)
    record("module_references", not unresolved, ", ".join(unresolved))

    invalid_names = [
        path.name
        for path in (infra / "modules").glob("*.bicep")
        if not NAME_PATTERN.fullmatch(path.stem)
    ]
    record("file_naming", not invalid_names, ", ".join(invalid_names))

    secret_findings: list[str] = []
    suspicious = re.compile(
        r"(?i)(password|clientSecret|apiKey)\s*[:=]\s*['\"](?!<|PLACEHOLDER)[^'\"]{4,}"
    )
    for path in infra.rglob("*"):
        if path.is_file() and path.suffix in {".bicep", ".json"}:
            if suspicious.search(path.read_text(encoding="utf-8")):
                secret_findings.append(str(path.relative_to(root)))
    record("no_obvious_secrets", not secret_findings, ", ".join(secret_findings))

    placeholders = [
        path for path in infra.rglob("*.bicep") if "PLACEHOLDER" in path.read_text(encoding="utf-8")
    ]
    readme = (
        (infra / "README.md").read_text(encoding="utf-8") if (infra / "README.md").exists() else ""
    )
    record("placeholders_documented", bool(placeholders) and "placeholder" in readme.lower())
    record("non_deploying_notice", "provisions nothing" in readme.lower())

    failed = sum(check["status"] == "failed" for check in checks)
    return {
        "overall_status": "passed" if failed == 0 else "failed",
        "checks": checks,
        "passed_checks": len(checks) - failed,
        "failed_checks": failed,
        "deployment_executed": False,
    }


def main() -> int:
    result = validate_infrastructure()
    print("Infrastructure scaffold static validation complete.")
    print(f"Status: {result['overall_status']}")
    print(f"Checks passed/failed: {result['passed_checks']}/{result['failed_checks']}")
    print("Azure deployment executed: no")
    for check in result["checks"]:
        print(f"- {check['name']}: {check['status']}")
    return 0 if result["overall_status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
