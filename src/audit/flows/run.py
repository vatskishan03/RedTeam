from __future__ import annotations

from pathlib import Path
from typing import Tuple

from audit.contracts import Finding
from audit.flows.fix import run_fix
from audit.flows.report import run_report
from audit.flows.scan import run_scan
from audit.flows.verify import run_verify
from audit.flows.baseline import run_baseline
from audit.flows.scorecard import build_scorecard
from audit.tools.run_state import RunPaths


def run_pipeline(
    target_path: Path,
    client,
    run_id: str | None = None,
    autofix: bool = False,
    use_heuristics: bool = False,
    max_rounds: int = 2,
    baseline: bool = True,
) -> RunPaths:
    run_paths, findings, _ = run_scan(
        target_path, client, run_id=run_id, use_heuristics=use_heuristics
    )
    baseline_findings = None
    if baseline and getattr(client, "available", False) and not use_heuristics:
        baseline_findings = run_baseline(
            target_path, client, run_id=run_paths.root.name
        )

    current_findings: list[Finding] = findings
    decisions = []
    verification = []
    for _ in range(max_rounds):
        run_paths, current_findings, _ = run_fix(
            target_path,
            client,
            run_id=run_paths.root.name,
            autofix=autofix,
            use_heuristics=use_heuristics,
        )
        run_paths, decisions, verification, updated = run_verify(
            target_path, client, run_id=run_paths.root.name
        )
        current_findings = updated
        if decisions and all(d.status == "fixed" for d in decisions):
            break

    build_scorecard(
        run_paths,
        current_findings,
        decisions,
        verification,
        baseline=baseline_findings,
    )
    run_report(target_path, client, run_id=run_paths.root.name)
    return run_paths
