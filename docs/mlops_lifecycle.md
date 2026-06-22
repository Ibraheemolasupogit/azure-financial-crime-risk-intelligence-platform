# MLOps Lifecycle

1. **Source control:** code, configuration, environment, schema, and documentation changes use reviewed pull requests and protected branches.
2. **Data validation:** contracts, relationships, ranges, distributions, provenance, and quarantine gates run before features.
3. **Feature generation:** versioned, prior-only transformations produce lineage and leakage evidence.
4. **Training:** pinned environments and chronological splits emit model, feature list, data/version references, and reproducibility metadata.
5. **Evaluation:** imbalance-aware metrics, threshold analysis, error slices, explanation reconstruction, robustness, bias/fairness, privacy, and security are reviewed.
6. **Registration:** an approved model package records owner, intended use, limitations, metrics, code/data/config/environment versions, and expiry.
7. **Approval gates:** Model Risk, Financial Crime, Data, Security, and Operations approve according to materiality; test-set tuning is prohibited.
8. **Deployment:** blue/green or canary releases use private authenticated endpoints, schema validation, load tests, observability, and automatic technical rollback criteria.
9. **Monitoring:** data/feature drift, score/performance shifts, latency/errors, explanation integrity, AML interactions, and downstream outcomes are monitored.
10. **Retraining:** approved triggers start a new candidate lifecycle; monitoring never silently changes a model, threshold, rule, or score weight.
11. **Rollback and incidents:** route traffic to a known-good model, retain evidence, assess affected decisions, and reprocess where authorised.
12. **Retirement:** disable endpoints, archive reproducibility evidence, update lineage/dependencies, and apply retention policy.

Fairness review must define relevant populations and lawful attributes with privacy/legal input; the synthetic project does not claim a completed production fairness assessment. Explanation validation confirms fidelity and usability but does not make associations causal. Incidents involving model abuse, corrupted data, missing lineage, or unsafe narratives follow documented runbooks.
