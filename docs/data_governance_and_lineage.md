# Data Governance and Lineage

## Lineage Chain

Synthetic raw customers, accounts, sessions, transactions, labels, and watchlist rows pass through validation into transaction/account/customer features. The fraud pipeline records feature list, split, model metadata, coefficients, predictions, threshold metrics, and explanations. AML alerts retain rule/config/evidence lineage. Customer risk rows retain component and weight evidence. Investigation packets cite selected predictions, alerts, scores, and explanations. Reporting facts reconcile to upstream counts and aggregate to governed KPIs.

## Governance Model

Owners are assigned by domain: Data Engineering owns ingestion/schema; Financial Crime Analytics owns AML controls and risk scoring; ML Engineering/Model Risk own model lifecycle; Investigation Operations owns case use; Analytics Engineering owns semantic measures; Security owns access/monitoring; Data Governance owns glossary, classification, retention, and lineage policy.

Raw schemas are versioned and changes require compatibility tests. Quality owners resolve failed contracts before downstream processing. Retention differs by legal basis, investigation need, model evidence, and local regulation; schedules and legal holds must be approved, automated, and auditable. Access follows purpose limitation, least privilege, environment separation, and periodic review.

## Purview Mapping

Purview collections represent environments and domains. Scans catalogue ADLS, Synapse, Azure ML, and Power BI; custom classifications cover pseudonymous customer/account IDs, fraud predictions, AML alerts, risk scores, model explanations, investigation narratives, and executive metrics. Business glossary terms link KPI, alert, score, and model definitions. Automated lineage is supplemented by pipeline-emitted manifests where connectors cannot express transformation detail.

The local data dictionary, feature dictionary, model metadata, reason codes, monitoring outputs, reporting dictionary, and lineage matrix are implementation evidence, not a substitute for a deployed governance programme.
