# Power BI-Ready Reporting Layer

Milestone 11 converts upstream synthetic outputs into a local star-schema-style import model: seven dimensions, nine facts, six aggregates, deterministic surrogate keys, 21 executive KPIs, an automated reporting dictionary, semantic relationships, DAX examples, and dashboard requirements.

Facts retain explicit grains and dimension keys. One-to-many, single-direction relationships keep filtering predictable. Counts reconcile to source transactions, AML alerts, customer scores, investigation cases, and monitoring alerts. Quality checks enforce unique keys, resolved foreign keys, date coverage, privacy exclusions, and expected grains.

The layer excludes names, dates of birth, addresses, and unnecessary evidence text. Natural IDs remain only where useful for controlled drill-through. CSV sensitivity labels distinguish analytical fields and restricted identifiers.

Run `python3 scripts/build_powerbi_outputs.py`. The output directory is `dashboard/powerbi_data/`; no `.pbix` file or Power BI Service connection is created. Future deployment may use ADLS, Synapse or Fabric, Power BI semantic models, Purview, Azure Monitor, Azure ML, and Azure AI Foundry.
