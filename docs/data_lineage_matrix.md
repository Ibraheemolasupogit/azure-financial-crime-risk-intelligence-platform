# Data Lineage Matrix

| Source artefact | Target artefact | Transformation | Owner | Quality control | Sensitivity | Azure mapping |
| --- | --- | --- | --- | --- | --- | --- |
| Synthetic generator config | `data/raw/*` | Deterministic entity/event generation | Data Engineering | Referential tests, seed | Synthetic pseudonymous | Event Hubs / ADLS raw |
| `data/raw/*` | Validation JSON/report | Schema, null, key, domain, relationship checks | Data Engineering | 45 validation checks | Synthetic pseudonymous | Functions / ADLS quarantine / Purview |
| Validated raw data | `data/processed/*_features.csv` | Prior-only aggregates and joins | Analytics Engineering | Leakage, uniqueness, dictionary | Derived behavioural | Synapse / ADLS curated |
| Transaction features + labels | Model + metrics + predictions | Chronological training and threshold analysis | ML Engineering | Test metrics, feature allowlist | Model-sensitive | Azure ML / registry |
| Transactions + configuration | AML alerts and summaries | Deterministic scenario evaluation | AML Analytics | Rule evidence and coverage | Investigation-sensitive | Stream Analytics / Functions / Synapse |
| Features + AML + predictions | Customer risk outputs | Weighted transparent components | Risk Analytics | Reconciliation, retrospective-only labels | Investigation-sensitive | Synapse / Azure ML |
| Model + predictions | Contributions and reason codes | Linear coefficient reconstruction | Model Risk | Probability reconstruction | Model-sensitive | Azure ML Responsible AI |
| Scores + alerts + explanations | Investigation packets/reports | Evidence selection and deterministic narrative | Investigation Operations | Grounding and safety checks | Highly restricted | AI Foundry / case platform |
| Platform outputs | Monitoring controls and alerts | Baseline/current comparison | MLOps | Threshold/status controls | Operational | Azure Monitor / Log Analytics |
| Validated domain outputs | Power BI facts/dimensions/aggregates | Surrogate keys, minimisation, reconciliation | Analytics Engineering | FK, count, privacy checks | Restricted analytical | Synapse / Power BI / Purview |

Every production row should carry source batch/event ID, processing version, timestamp, configuration/model version, and correlation ID where applicable. Retention and access policy are jurisdiction- and institution-specific.
