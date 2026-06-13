from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


EXPECTED_DIRECTORIES = [
    "configs",
    "data",
    "data/raw",
    "data/processed",
    "data/samples",
    "src",
    "src/data_generation",
    "src/ingestion",
    "src/validation",
    "src/features",
    "src/models",
    "src/risk_scoring",
    "src/aml_rules",
    "src/explainability",
    "src/genai",
    "src/reporting",
    "src/monitoring",
    "docs",
    "diagrams",
    "outputs",
    "outputs/reports",
    "dashboard",
    "tests",
    "scripts",
    ".github/workflows",
]

EXPECTED_FILES = [
    "README.md",
    "requirements.txt",
    "pyproject.toml",
    ".gitignore",
    "configs/project_config.yaml",
    "docs/project_overview.md",
    "docs/azure_service_mapping.md",
    "docs/milestone_plan.md",
    "docs/data_privacy_and_synthetic_data.md",
    "diagrams/architecture_placeholder.md",
    "scripts/run_all_local.sh",
    "tests/test_repo_structure.py",
    ".github/workflows/ci.yml",
    "src/__init__.py",
    "src/data_generation/__init__.py",
    "src/ingestion/__init__.py",
    "src/validation/__init__.py",
    "src/features/__init__.py",
    "src/models/__init__.py",
    "src/risk_scoring/__init__.py",
    "src/aml_rules/__init__.py",
    "src/explainability/__init__.py",
    "src/genai/__init__.py",
    "src/reporting/__init__.py",
    "src/monitoring/__init__.py",
]


def test_expected_directories_exist() -> None:
    missing = [path for path in EXPECTED_DIRECTORIES if not (ROOT / path).is_dir()]
    assert not missing, f"Missing expected directories: {missing}"


def test_expected_files_exist() -> None:
    missing = [path for path in EXPECTED_FILES if not (ROOT / path).is_file()]
    assert not missing, f"Missing expected files: {missing}"
