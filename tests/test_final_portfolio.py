import json
from pathlib import Path

import pandas as pd
from scripts.run_final_audit import run_final_audit
from scripts.validate_infrastructure import EXPECTED_FILES, validate_infrastructure

ROOT = Path(__file__).resolve().parents[1]


def test_architecture_contains_required_azure_services() -> None:
    paths = [
        ROOT / "diagrams/azure_reference_architecture.md",
        ROOT / "diagrams/azure_reference_architecture.mmd",
    ]
    assert all(path.is_file() for path in paths)
    architecture = paths[1].read_text(encoding="utf-8")
    for service in [
        "Azure Event Hubs",
        "Azure Data Lake Storage Gen2",
        "Azure Synapse Analytics",
        "Azure Machine Learning",
        "Azure AI Foundry",
        "Power BI",
        "Microsoft Purview",
        "Azure Key Vault",
    ]:
        assert service in architecture


def test_complete_adr_set_has_required_sections() -> None:
    adrs = sorted((ROOT / "docs/architecture_decisions").glob("ADR-*.md"))
    assert len(adrs) == 10
    for path in adrs:
        text = path.read_text(encoding="utf-8")
        for section in [
            "Status",
            "Context",
            "Decision",
            "Alternatives Considered",
            "Consequences",
            "Security Implications",
            "Cost Implications",
            "Local Implementation Mapping",
            "Azure Production Mapping",
        ]:
            assert f"## {section}" in text


def test_infrastructure_modules_and_static_validation() -> None:
    assert all((ROOT / "infra" / path).is_file() for path in EXPECTED_FILES)
    result = validate_infrastructure(ROOT)
    assert result["overall_status"] == "passed"
    assert result["deployment_executed"] is False


def test_no_obvious_secrets_in_iac() -> None:
    forbidden = ["password:", "client_secret:", "api_key:"]
    text = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "infra").rglob("*.*"))
    assert not any(token in text.lower() for token in forbidden)


def test_azure_ml_mapping_files_exist() -> None:
    expected = [
        "environments/fraud-model-conda.yaml",
        "jobs/train_fraud_model.yml",
        "jobs/score_batch.yml",
        "endpoints/managed-endpoint.yml",
        "endpoints/managed-deployment.yml",
        "components/feature_engineering.yml",
        "components/train_model.yml",
        "components/evaluate_model.yml",
        "pipelines/fraud_training_pipeline.yml",
        "README.md",
    ]
    assert all((ROOT / "azureml" / path).is_file() for path in expected)


def test_security_governance_and_runbooks_exist() -> None:
    required_docs = [
        "security_architecture.md",
        "threat_model.md",
        "data_governance_and_lineage.md",
        "data_lineage_matrix.md",
        "mlops_lifecycle.md",
        "release_strategy.md",
    ]
    assert all((ROOT / "docs" / path).is_file() for path in required_docs)
    assert len(list((ROOT / "docs/runbooks").glob("runbook-*.md"))) == 8


def test_readme_has_flagship_sections_and_honest_disclaimers() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    sections = [
        "Executive Summary",
        "Architecture",
        "Platform Capabilities",
        "End-to-End Lifecycle",
        "Headline Results",
        "Azure Service Mapping",
        "Power BI-Ready Analytics",
        "Security, Governance and MLOps",
        "Quick Start",
        "Repository Structure",
        "Testing and Quality",
        "Known Limitations",
        "Target Roles",
        "Portfolio Guides",
        "Synthetic Data Disclaimer",
    ]
    assert all(f"## {section}" in text for section in sections)
    required_links = [
        "diagrams/azure_reference_architecture.md",
        "diagrams/azure_reference_architecture.mmd",
        "docs/architecture_decisions/",
        "docs/portfolio_evidence.md",
        "docs/recruiter_summary.md",
        "docs/interview_guide.md",
        "docs/demo_guide.md",
    ]
    for path in required_links:
        assert f"]({path})" in text
        assert (ROOT / path).exists()
    for statement in [
        "Fraud performance is weak",
        "false-positive",
        "no live Azure",
        "synthetic",
    ]:
        assert statement.lower() in text.lower()


def test_portfolio_guides_exist_and_evidence_paths_resolve() -> None:
    for name in ["recruiter_summary.md", "interview_guide.md", "demo_guide.md"]:
        assert (ROOT / "docs" / name).is_file()
    evidence = (ROOT / "docs/portfolio_evidence.md").read_text(encoding="utf-8")
    for path in ["src/", "scripts/", "pyproject.toml", "docs/streaming_design.md"]:
        assert path in evidence
        assert (ROOT / path).exists()


def test_final_status_and_audit_outputs_are_valid_json() -> None:
    for path in [
        ROOT / "outputs/final_project_status.json",
        ROOT / "outputs/final_quality_audit.json",
    ]:
        data = json.loads(path.read_text(encoding="utf-8"))
        assert isinstance(data, dict)
    audit = json.loads((ROOT / "outputs/final_quality_audit.json").read_text(encoding="utf-8"))
    assert audit["overall_status"] == "passed"


def test_final_audit_passes_without_runtime_recursion() -> None:
    result = run_final_audit(run_runtime_checks=False)
    assert result["overall_status"] == "passed"
    assert result["milestones_represented"] == 12
    assert result["network_calls_made"] is False
    assert result["azure_resources_deployed"] is False


def test_reporting_outputs_exclude_prohibited_personal_columns() -> None:
    prohibited = {"first_name", "last_name", "date_of_birth", "address", "email", "phone_number"}
    for path in (ROOT / "dashboard/powerbi_data").glob("*.csv"):
        assert not (set(pd.read_csv(path, nrows=0).columns) & prohibited)


def test_project_requires_neither_network_calls_nor_pbix() -> None:
    assert not list(ROOT.rglob("*.pbix"))
    function_text = (ROOT / "deployment/functions/function_app_placeholder.py").read_text(
        encoding="utf-8"
    )
    assert "requests" not in function_text
    assert "network_call_made" in function_text


def test_synthetic_disclaimers_are_prominent() -> None:
    for path in [ROOT / "README.md", ROOT / "infra/README.md", ROOT / "azureml/README.md"]:
        assert "synthetic" in path.read_text(encoding="utf-8").lower()
