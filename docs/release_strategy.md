# Release Strategy

Use short-lived feature branches, reviewed pull requests, protected main, required CI, and signed/tagged releases. Trunk-based development is preferred; release branches are reserved for supported production lines. Semantic versioning covers platform releases; models use immutable registry versions plus model-card metadata; configurations use source-controlled versions and content hashes.

CI gates formatting/lint, tests, deterministic local workflow, data/feature/model quality, explanation and GenAI safety, infrastructure static validation, and final audit. Dependency and secret findings block according to severity. Promotion from dev to test to production references the same immutable artifacts and requires environment-specific approval and evidence.

Managed endpoints use blue/green or low-volume canary traffic with technical and business guardrails. Rollback restores the previous model, code, configuration, and routing atomically; schema compatibility and downstream reprocessing are assessed. Releases retain commit, build, test, SBOM/dependency evidence where available, IaC plan, approvers, model/config versions, metrics, monitoring baseline, and change ticket.

No workflow in this repository deploys Azure resources. Real deployment requires change-management, segregation-of-duties, security, model-risk, financial-crime, privacy, and operational approvals appropriate to the institution.
