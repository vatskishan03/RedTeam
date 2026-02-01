from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from audit.agents import ArbiterAgent
from audit.contracts import Decision, Finding, Patch, VerificationResult
from audit.flows.utils import apply_decisions
from audit.tools.jsonio import read_json, write_json
from audit.tools.linters import run_bandit, run_pytest, run_ruff
from audit.tools.run_state import RunPaths, ensure_run_dir


def _load_findings(run_paths: RunPaths) -> List[Finding]:
    payload = read_json(run_paths.findings, default=[])
    return [Finding.model_validate(item) for item in payload]


def _load_patches(run_paths: RunPaths) -> List[Patch]:
    payload = read_json(run_paths.patches, default=[])
    return [Patch.model_validate(item) for item in payload]


def run_verify(
    target_path: Path,
    client,
    run_id: str | None = None,
) -> Tuple[RunPaths, List[Decision], List[VerificationResult], List[Finding]]:
    run_paths = ensure_run_dir(run_id)
    findings = _load_findings(run_paths)
    patches = _load_patches(run_paths)

    results = [
        run_bandit(target_path),
        run_ruff(target_path),
        run_pytest(target_path),
    ]
    verification = [VerificationResult.model_validate(r.__dict__) for r in results]
    write_json(run_paths.verification, [v.model_dump() for v in verification])

    decisions: List[Decision] = []
    if getattr(client, "available", False):
        agent = ArbiterAgent(client)
        decisions = agent.run(findings, patches, verification)
    else:
        status = "fixed" if all(r.exit_code == 0 for r in results) else "rejected"
        decisions = [Decision(id=f.id, status=status, reason="Tool-only verdict") for f in findings]

    write_json(run_paths.decisions, [d.model_dump() for d in decisions])
    updated_findings = apply_decisions(findings, decisions)
    write_json(run_paths.findings, [f.model_dump() for f in updated_findings])

    return run_paths, decisions, verification, updated_findings
