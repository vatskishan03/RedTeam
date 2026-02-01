from __future__ import annotations

from pathlib import Path
from typing import List

from audit.agents import ReporterAgent
from audit.contracts import Decision, Finding, Patch, VerificationResult
from audit.tools.jsonio import read_json
from audit.tools.run_state import RunPaths, ensure_run_dir


def _load_findings(run_paths: RunPaths) -> List[Finding]:
    payload = read_json(run_paths.findings, default=[])
    return [Finding.model_validate(item) for item in payload]


def _load_patches(run_paths: RunPaths) -> List[Patch]:
    payload = read_json(run_paths.patches, default=[])
    return [Patch.model_validate(item) for item in payload]


def _load_verification(run_paths: RunPaths) -> List[VerificationResult]:
    payload = read_json(run_paths.verification, default=[])
    return [VerificationResult.model_validate(item) for item in payload]


def _load_decisions(run_paths: RunPaths) -> List[Decision]:
    payload = read_json(run_paths.decisions, default=[])
    return [Decision.model_validate(item) for item in payload]


def run_report(target_path: Path, client, run_id: str | None = None) -> RunPaths:
    run_paths = ensure_run_dir(run_id)
    findings = _load_findings(run_paths)
    patches = _load_patches(run_paths)
    verification = _load_verification(run_paths)
    decisions = _load_decisions(run_paths)

    if getattr(client, "available", False):
        agent = ReporterAgent(client)
        report = agent.run(
            str(target_path),
            findings,
            patches,
            verification,
            decisions,
        )
    else:
        report = _fallback_report(str(target_path), findings, verification, decisions)

    run_paths.report.write_text(report, encoding="utf-8")
    return run_paths


def _fallback_report(
    target_path: str,
    findings: List[Finding],
    verification: List[VerificationResult],
    decisions: List[Decision],
) -> str:
    total = len(findings)
    fixed = len([d for d in decisions if d.status == "fixed"])
    lines = ["# Security Report", "", f"Target: `{target_path}`", "", "## Summary"]
    lines.append(f"- Findings: {total}")
    lines.append(f"- Fixed: {fixed}")
    lines.append("")
    lines.append("## Findings")
    for finding in findings:
        lines.append(
            f"- {finding.id} ({finding.severity}) {finding.title} at {finding.file}:{finding.line}"
        )
    lines.append("")
    lines.append("## Verification")
    for result in verification:
        lines.append(f"- {result.name}: exit {result.exit_code}")
    return "\n".join(lines)
