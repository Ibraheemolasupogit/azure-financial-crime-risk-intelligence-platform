# ADR-007: Azure AI Foundry for Investigations

## Status
Proposed, subject to responsible-AI and legal approval.

## Context
Investigators can benefit from grounded summaries, but generated text can hallucinate, overstate suspicion, or expose data.

## Decision
Use Azure AI Foundry/Azure OpenAI only behind evidence-grounding, content, access, logging, and mandatory human-approval controls.

## Alternatives Considered
Template-only generation is safer but less flexible; unmanaged external APIs create unacceptable governance gaps.

## Consequences
Prompts, sources, outputs, model versions, reviewer decisions, and safety evaluations require retention and monitoring.

## Security Implications
Use private networking, managed identity, minimised prompts, prompt-injection controls, and prohibit autonomous filing or action.

## Cost Implications
Token use, model tier, retrieval, evaluations, logging, and throughput reservations drive cost.

## Local Implementation Mapping
Deterministic templates and disabled prompt payloads demonstrate grounding without any model or network call.

## Azure Production Mapping
Foundry projects orchestrate approved deployments and evaluations; Key Vault, Monitor, and Purview govern supporting assets.
