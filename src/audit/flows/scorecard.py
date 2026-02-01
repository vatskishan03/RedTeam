from __future__ import annotations

from typing import List, Dict

from audit.contracts import Decision, Finding, VerificationResult
from audit.tools.jsonio import write_json
from audit.tools.run_state import RunPaths


def _key(finding: Finding) -> str:
    return f"{finding.file}:{finding.line}:{finding.title}"


def build_scorecard(
    run_paths: RunPaths,
    findings: List[Finding],
    decisions: List[Decision],
    verification: List[VerificationResult],
    baseline: List[Finding] | None = None,
) -> Dict[str, object]:
    total = len(findings)
    fixed = len([d for d in decisions if d.status == "fixed"])
    rejected = len([d for d in decisions if d.status == "rejected"])
    tool_pass = all(v.exit_code == 0 for v in verification) if verification else False

    payload: Dict[str, object] = {
        "findings_total": total,
        "fixed": fixed,
        "rejected": rejected,
        "fix_rate": round((fixed / total) if total else 0.0, 2),
        "tools_pass": tool_pass,
    }

    if baseline is not None:
        base_total = len(baseline)
        delta = total - base_total
        overlap = len({ _key(f) for f in findings } & { _key(b) for b in baseline })
        payload.update(
            {
                "baseline_total": base_total,
                "delta_vs_baseline": delta,
                "baseline_overlap": overlap,
            }
        )

    write_json(run_paths.scorecard, payload)
    return payload
