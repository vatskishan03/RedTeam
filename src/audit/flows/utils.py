from __future__ import annotations

from typing import List

from audit.contracts import Decision, Finding, Patch


def normalize_findings(findings: List[Finding]) -> List[Finding]:
    normalized: List[Finding] = []
    for idx, finding in enumerate(findings, start=1):
        fid = finding.id or f"F-{idx:03d}"
        severity = finding.severity.lower()
        if severity not in {"low", "medium", "high", "critical"}:
            severity = "medium"
        normalized.append(
            finding.model_copy(update={"id": fid, "severity": severity})
        )
    return normalized


def normalize_patches(patches: List[Patch], findings: List[Finding]) -> List[Patch]:
    valid_ids = {f.id for f in findings}
    normalized: List[Patch] = []
    for patch in patches:
        if patch.id in valid_ids:
            normalized.append(patch)
    return normalized


def apply_decisions(findings: List[Finding], decisions: List[Decision]) -> List[Finding]:
    decision_map = {d.id: d for d in decisions}
    updated: List[Finding] = []
    for finding in findings:
        decision = decision_map.get(finding.id)
        if decision:
            updated.append(finding.model_copy(update={"status": decision.status}))
        else:
            updated.append(finding)
    return updated
