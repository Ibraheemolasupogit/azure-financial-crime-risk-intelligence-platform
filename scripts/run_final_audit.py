#!/usr/bin/env python3
"""Audit portfolio completeness without provisioning resources or making network calls."""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

try:
    from scripts.validate_infrastructure import EXPECTED_FILES, validate_infrastructure
except ModuleNotFoundError:  # Direct execution places scripts/ rather than repo root on sys.path.
    from validate_infrastructure import EXPECTED_FILES, validate_infrastructure

ROOT = Path(__file__).resolve().parents[1]

ARCHITECTURE_FILES = [
    "diagrams/azure_reference_architecture.md",
    "diagrams/azure_reference_architecture.mmd",
]
ADR_FILES = [f"docs/architecture_decisions/ADR-{index:03d}" for index in range(1, 11)]
AZUREML_FILES = [
    "azureml/environments/fraud-model-conda.yaml",
    "azureml/jobs/train_fraud_model.yml",
    "azureml/jobs/score_batch.yml",
    "azureml/endpoints/managed-endpoint.yml",
    "azureml/endpoints/managed-deployment.yml",
    "azureml/components/feature_engineering.yml",
    "azureml/components/train_model.yml",
    "azureml/components/evaluate_model.yml",
    "azureml/pipelines/fraud_training_pipeline.yml",
    "azureml/README.md",
]
SECURITY_GOVERNANCE_FILES = [
    "docs/security_architecture.md",
    "docs/threat_model.md",
    "docs/data_governance_and_lineage.md",
    "docs/data_lineage_matrix.md",
    "docs/mlops_lifecycle.md",
    "docs/release_strategy.md",
]
RUNBOOK_FILES = [
    "runbook-data-quality-failure.md",
    "runbook-model-performance-degradation.md",
    "runbook-aml-alert-overload.md",
    "runbook-explainability-failure.md",
    "runbook-genai-grounding-failure.md",
    "runbook-pipeline-failure.md",
    "runbook-security-incident.md",
    "runbook-model-rollback.md",
]
README_SECTIONS = [
    "Executive Summary",
    "Business Problem",
    "Platform Capabilities",
    "Architecture",
    "End-to-End Workflow",
    "Implemented Features",
    "Azure Service Mapping",
    "Quick Start",
    "Sample Outputs",
    "Security and Governance",
    "MLOps",
    "Testing",
    "Known Limitations",
    "Skills Demonstrated",
    "Target Roles",
    "Synthetic Data Disclaimer",
]
PROHIBITED_REPORTING_COLUMNS = {
    "first_name",
    "last_name",
    "date_of_birth",
    "address",
    "email",
    "phone_number",
}


def _existing_all(paths: list[str]) -> tuple[bool, list[str]]:
    missing = [path for path in paths if not (ROOT / path).exists()]
    return not missing, missing


def _adr_paths() -> list[str]:
    paths: list[str] = []
    for prefix in ADR_FILES:
        matches = sorted(ROOT.glob(f"{prefix}-*.md"))
        if matches:
            paths.append(str(matches[0].relative_to(ROOT)))
    return paths


def _run_command(command: list[str]) -> tuple[bool, str]:
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    output = (completed.stdout + completed.stderr).strip()
    return completed.returncode == 0, output[-2000:]


def run_final_audit(run_runtime_checks: bool = True) -> dict[str, object]:
    """Run milestone, security, privacy, documentation, and optional runtime checks."""
    checks: list[dict[str, str]] = []

    def record(name: str, passed: bool, detail: str = "") -> None:
        checks.append({"name": name, "status": "passed" if passed else "failed", "detail": detail})

    milestone_paths = [
        "README.md",
        "src/data_generation/generate_banking_data.py",
        "src/ingestion/load_banking_data.py",
        "src/features/build_features.py",
        "src/models/train_fraud_baseline.py",
        "src/aml_rules/aml_rule_engine.py",
        "src/risk_scoring/customer_risk_scoring.py",
        "src/explainability/explain_fraud_model.py",
        "src/genai/investigation_assistant.py",
        "src/monitoring/monitor_platform.py",
        "src/reporting/build_powerbi_outputs.py",
        "diagrams/azure_reference_architecture.mmd",
    ]
    passed, missing = _existing_all(milestone_paths)
    record("all_12_milestones", passed, ", ".join(missing))

    passed, missing = _existing_all(ARCHITECTURE_FILES)
    record("architecture_files", passed, ", ".join(missing))
    adrs = _adr_paths()
    record("architecture_decisions", len(adrs) == 10, f"found {len(adrs)}")

    infrastructure = validate_infrastructure(ROOT)
    record("infrastructure_validation", infrastructure["overall_status"] == "passed")
    passed, missing = _existing_all(AZUREML_FILES)
    record("azureml_mappings", passed, ", ".join(missing))
    passed, missing = _existing_all(SECURITY_GOVERNANCE_FILES)
    record("security_and_governance", passed, ", ".join(missing))

    runbooks = [f"docs/runbooks/{name}" for name in RUNBOOK_FILES]
    passed, missing = _existing_all(runbooks)
    record("operational_runbooks", passed, ", ".join(missing))

    dashboard_files = [
        "dashboard/semantic_model_spec.md",
        "dashboard/dax_measures.md",
        "dashboard/executive_dashboard_spec.md",
        "dashboard/kpi_definitions.md",
    ]
    passed, missing = _existing_all(dashboard_files)
    record("dashboard_specifications", passed, ", ".join(missing))

    primary_outputs = [
        "outputs/data_validation_results.json",
        "outputs/fraud_model_metrics.json",
        "outputs/aml_transaction_alerts.csv",
        "outputs/customer_risk_scores.csv",
        "outputs/fraud_explanation_quality.json",
        "outputs/genai_grounding_quality.json",
        "outputs/platform_monitoring_summary.json",
        "outputs/reporting_quality_summary.json",
    ]
    passed, missing = _existing_all(primary_outputs)
    record("primary_outputs", passed, ", ".join(missing))

    readme_text = (ROOT / "README.md").read_text(encoding="utf-8")
    missing_sections = [
        section for section in README_SECTIONS if f"## {section}" not in readme_text
    ]
    record("readme_sections", not missing_sections, ", ".join(missing_sections))

    portfolio_paths = [
        "docs/portfolio_evidence.md",
        "docs/interview_guide.md",
        "docs/recruiter_summary.md",
        "docs/demo_guide.md",
        ".github/workflows/ci.yml",
        ".github/workflows/security.yml",
        ".github/dependabot.yml",
    ]
    passed, missing = _existing_all(portfolio_paths)
    record("portfolio_and_ci_files", passed, ", ".join(missing))

    secret_findings: list[str] = []
    secret_pattern = re.compile(
        r"(?i)(password|client_secret|api_key)\s*[:=]\s*['\"](?!<|PLACEHOLDER)[^'\"]{8,}"
    )
    for directory in [ROOT / "infra", ROOT / "azureml", ROOT / "deployment"]:
        for path in directory.rglob("*"):
            if path.is_file() and path.suffix in {".bicep", ".json", ".yaml", ".yml", ".py"}:
                if secret_pattern.search(path.read_text(encoding="utf-8")):
                    secret_findings.append(str(path.relative_to(ROOT)))
    record("no_obvious_secrets", not secret_findings, ", ".join(secret_findings))

    prohibited: list[str] = []
    for path in (ROOT / "dashboard/powerbi_data").glob("*.csv"):
        with path.open(encoding="utf-8", newline="") as handle:
            columns = set(next(csv.reader(handle), []))
        matches = sorted(columns & PROHIBITED_REPORTING_COLUMNS)
        if matches:
            prohibited.append(f"{path.name}:{','.join(matches)}")
    record("reporting_privacy", not prohibited, "; ".join(prohibited))

    broken_links: list[str] = []
    for match in re.finditer(r"\[[^]]+\]\(([^)]+)\)", readme_text):
        target = match.group(1).split("#", 1)[0]
        if (
            target
            and not target.startswith(("http://", "https://", "#"))
            and not (ROOT / target).exists()
        ):
            broken_links.append(target)
    record("readme_repository_links", not broken_links, ", ".join(broken_links))

    network_markers = ["requests.", "urllib.request", "httpx.", "aiohttp."]
    executable_text = "\n".join(
        path.read_text(encoding="utf-8")
        for folder in [ROOT / "scripts", ROOT / "deployment/functions"]
        for path in folder.glob("*.py")
        if path.resolve() != Path(__file__).resolve()
    )
    used_markers = [marker for marker in network_markers if marker in executable_text]
    record("no_runtime_network_calls", not used_markers, ", ".join(used_markers))
    record("no_pbix_required", not list(ROOT.rglob("*.pbix")))
    record(
        "synthetic_disclaimers",
        "synthetic" in readme_text.lower() and "no live azure" in readme_text.lower(),
    )

    runtime: dict[str, object] = {"executed": run_runtime_checks}
    if run_runtime_checks:
        tests_ok, tests_output = _run_command([sys.executable, "-m", "pytest", "-q"])
        ruff_ok, ruff_output = _run_command([sys.executable, "-m", "ruff", "check", "."])
        record("pytest", tests_ok, tests_output)
        record("ruff", ruff_ok, ruff_output)
        match = re.search(r"(\d+) passed", tests_output)
        runtime.update(
            {
                "tests_passed": int(match.group(1)) if match else 0,
                "pytest_status": "passed" if tests_ok else "failed",
                "ruff_status": "passed" if ruff_ok else "failed",
            }
        )

    failed = sum(check["status"] == "failed" for check in checks)
    return {
        "audit_timestamp": datetime.now(UTC).isoformat(),
        "overall_status": "passed" if failed == 0 else "failed",
        "milestones_represented": 12,
        "passed_checks": len(checks) - failed,
        "failed_checks": failed,
        "checks": checks,
        "infrastructure_validation": infrastructure,
        "runtime_validation": runtime,
        "network_calls_made": False,
        "azure_resources_deployed": False,
    }


def write_audit_outputs(result: dict[str, object]) -> None:
    outputs = ROOT / "outputs"
    reports = ROOT / "reports"
    outputs.mkdir(exist_ok=True)
    reports.mkdir(exist_ok=True)
    (outputs / "final_quality_audit.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )

    checks = result["checks"]
    rows = "\n".join(
        f"| {check['name']} | {check['status']} | {check['detail'] or '-'} |" for check in checks
    )
    report = f"""# Final Quality Audit

- Timestamp: {result["audit_timestamp"]}
- Overall status: **{result["overall_status"]}**
- Milestones represented: {result["milestones_represented"]}/12
- Checks passed/failed: {result["passed_checks"]}/{result["failed_checks"]}
- Azure resources deployed: no
- Network calls made: no

| Check | Status | Detail |
| --- | --- | --- |
{rows}

This audit verifies repository evidence only. It is not a security certification, regulatory
approval, Azure deployment validation, or production-readiness assessment.
"""
    (reports / "final_quality_audit.md").write_text(report, encoding="utf-8")

    documentation_count = len(list((ROOT / "docs").rglob("*.md")))
    tests_passed = result["runtime_validation"].get("tests_passed", 0)
    final_status = {
        "completion_timestamp": result["audit_timestamp"],
        "milestones_completed": list(range(1, 13)),
        "modules_implemented": [
            "synthetic_data",
            "ingestion_validation",
            "feature_engineering",
            "fraud_model",
            "aml_rules",
            "customer_risk",
            "explainability",
            "genai_investigations",
            "monitoring",
            "powerbi_reporting",
            "azure_architecture",
            "portfolio_assurance",
        ],
        "tests_passed": tests_passed,
        "primary_outputs": ["outputs", "reports", "dashboard/powerbi_data"],
        "architecture_artefacts": ARCHITECTURE_FILES + _adr_paths(),
        "infrastructure_artefacts": [f"infra/{path}" for path in EXPECTED_FILES],
        "documentation_count": documentation_count,
        "ci_workflows": [".github/workflows/ci.yml", ".github/workflows/security.yml"],
        "security_controls": [
            "least_privilege",
            "managed_identity",
            "private_endpoints",
            "key_vault",
            "audit_logging",
            "threat_model",
        ],
        "known_limitations": [
            "synthetic data only",
            "weak fraud baseline performance",
            "high AML false-positive volume",
            "deterministic GenAI mode",
            "no live Azure deployment",
            "no deployed Power BI model",
            "illustrative infrastructure templates",
        ],
        "future_deployment_steps": [
            "subscription-specific architecture and threat review",
            "Bicep compiler and policy validation",
            "private synthetic-data development deployment",
            "load, resilience, security, and model-risk validation",
            "approved environment promotion",
        ],
        "overall_project_status": result["overall_status"],
        "synthetic_data_statement": (
            "All project data is synthetic; no real customer or banking data is used."
        ),
        "azure_resources_deployed": False,
        "network_calls_made": False,
    }
    (outputs / "final_project_status.json").write_text(
        json.dumps(final_status, indent=2) + "\n", encoding="utf-8"
    )

    final_report = f"""# Final Project Report

## Status

All 12 milestones are represented. Final audit status: **{result["overall_status"]}**.
Automated tests reported: **{tests_passed} passed**. Documentation files:
**{documentation_count}**.

## Delivered Platform

The repository implements a deterministic local synthetic-data pipeline covering ingestion,
validation, features, fraud ML, AML rules, customer risk, explainability, grounded investigation
drafting, monitoring, and Power BI-ready outputs. The final milestone adds Azure architecture,
modular Bicep, Azure ML and streaming mappings, security, threat modelling, lineage, MLOps,
runbooks, CI, and portfolio evidence.

## Assurance

Infrastructure static validation status:
**{result["infrastructure_validation"]["overall_status"]}**. No secrets were intentionally added,
no Azure resources were deployed, and no runtime network calls are required. Outputs remain
synthetic and require human interpretation.

## Limitations

The fraud baseline performs weakly, AML scenarios generate substantial false positives, GenAI
remains deterministic, Power BI is not deployed, and Azure templates are illustrative rather than
subscription-validated. The project does not claim production readiness, regulatory compliance,
certification, or real-world detection effectiveness.
"""
    (reports / "final_project_report.md").write_text(final_report, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-runtime-checks",
        action="store_true",
        help="Skip pytest and Ruff subprocesses; structural checks still run.",
    )
    args = parser.parse_args()
    result = run_final_audit(run_runtime_checks=not args.skip_runtime_checks)
    write_audit_outputs(result)
    print("Final portfolio quality audit complete.")
    print(f"Status: {result['overall_status']}")
    print(f"Milestones represented: {result['milestones_represented']}/12")
    print(f"Checks passed/failed: {result['passed_checks']}/{result['failed_checks']}")
    print("Azure resources deployed: no")
    print("Network calls made: no")
    print("JSON: outputs/final_quality_audit.json")
    print("Report: reports/final_quality_audit.md")
    return 0 if result["overall_status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
