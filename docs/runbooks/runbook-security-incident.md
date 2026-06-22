# Runbook: Security Incident

## Trigger
Suspected unauthorised access, secret exposure, malicious data/model change, exfiltration, privilege escalation, or control bypass.

## Severity
Use the organisation's security classification; assume high until scope and exposure are understood.

## Initial Checks
Engage security response, verify alert without altering evidence, identify identities/assets/time window, and establish incident command.

## Containment
Revoke/disable compromised identities or tokens, isolate endpoints/workloads, block egress, rotate secrets, and preserve logs/snapshots.

## Investigation
Build a timeline from identity, network, data, CI/CD, model, AI, dashboard, and administrative logs; assess decisions and data exposure.

## Remediation
Remove persistence, patch cause, restore known-good artifacts, reissue credentials, reprocess affected outputs, and strengthen controls.

## Validation
Security verifies eradication; owners validate integrity, access, monitoring, lineage, and business outputs before recovery.

## Escalation
SOC/CSIRT, Legal, Privacy, Compliance, executive risk, regulators/customers only through approved obligations and channels.

## Evidence to Retain
Immutable logs, images, hashes, access records, affected assets/data, actions, approvals, communications, and chain of custody.

## Post-Incident Review
Complete root cause, impact, disclosure assessment, threat/control updates, and tracked remediation.
