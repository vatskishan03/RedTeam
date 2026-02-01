from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from audit.agents import ArbiterAgent
from audit.contracts import Decision, Finding, Patch, VerificationResult
from audit.flows.utils import apply_decisions
from audit.tools.jsonio import read_json, write_json
from audit.tools.linters import run_bandit, run_pytest, run_ruff
from audit.tools.run_state import RunPaths, ensure_run_dir
from audit.flows.reattack import run_reattack


def _load_findings(run_paths: RunPaths) -> List[Finding]:
    payload = read_json(run_paths.findings, default=[])
    return [Finding.model_validate(item) for item in payload]


def _load_patches(run_paths: RunPaths) -> List[Patch]:
    payload = read_json(run_paths.patches, default=[])
    return [Patch.model_validate(item) for item in payload]


def _load_apply_results(run_paths: RunPaths) -> List[dict]:
    payload = read_json(run_paths.apply, default=[])
    return payload if isinstance(payload, list) else []


def _heuristic_decisions(
    findings: List[Finding],
    apply_results: List[dict],
    verification: List[VerificationResult],
    reattack_findings: List[Finding],
) -> List[Decision]:
    def _similar_evidence(a: str, b: str) -> bool:
        a = (a or "").strip()
        b = (b or "").strip()
        if not a or not b:
            return False
        short, long = (a, b) if len(a) <= len(b) else (b, a)
        return short in long

    apply_map = {str(item.get("id")): item for item in apply_results if isinstance(item, dict)}
    tools_note = ", ".join(
        f"{v.name}={v.exit_code}" for v in verification if v.exit_code != 0
    )
    decisions: List[Decision] = []
    for f in findings:
        applied = apply_map.get(f.id, {})
        applied_ok = bool(applied.get("ok", False))
        # Match by coarse key since heuristic/reattack IDs may differ.
        still_present = any(
            (
                rf.cwe == f.cwe
                and Path(rf.file).name == Path(f.file).name
                and (
                    _similar_evidence(rf.evidence, f.evidence)
                    or rf.title.lower() == f.title.lower()
                )
            )
            for rf in reattack_findings
        )
        if still_present:
            decisions.append(
                Decision(
                    id=f.id,
                    status="rejected",
                    reason="Re-attack still detects this issue in the post-fix code.",
                )
            )
            continue
        if not applied_ok and apply_results:
            decisions.append(
                Decision(
                    id=f.id,
                    status="rejected",
                    reason="Patch did not apply cleanly; cannot validate a fix.",
                )
            )
            continue

        reason = "No re-attack evidence for this finding after applying patches."
        if tools_note:
            reason = f"{reason} Verification tools failing: {tools_note}."
        decisions.append(Decision(id=f.id, status="fixed", reason=reason))
    return decisions


def run_verify(
    target_path: Path,
    client,
    run_id: str | None = None,
    reattack: bool = True,
    use_heuristics: bool = False,
) -> Tuple[RunPaths, List[Decision], List[VerificationResult], List[Finding]]:
    run_paths = ensure_run_dir(run_id)
    findings = _load_findings(run_paths)
    patches = _load_patches(run_paths)
    apply_results = _load_apply_results(run_paths)

    results = [
        run_bandit(target_path),
        run_ruff(target_path),
        run_pytest(target_path),
    ]
    verification = [VerificationResult.model_validate(r.__dict__) for r in results]
    write_json(run_paths.verification, [v.model_dump() for v in verification])

    decisions: List[Decision] = []
    reattack_findings: List[Finding] = []
    if reattack:
        reattack_findings = run_reattack(
            target_path, client, run_id=run_paths.root.name, use_heuristics=use_heuristics
        )

    if getattr(client, "available", False) and not use_heuristics:
        try:
            agent = ArbiterAgent(client)
            decisions = agent.run(
                findings,
                patches,
                verification,
                reattack=reattack_findings,
                apply_results=apply_results,
            )
        except Exception:
            decisions = _heuristic_decisions(findings, apply_results, verification, reattack_findings)
    else:
        decisions = _heuristic_decisions(findings, apply_results, verification, reattack_findings)

    write_json(run_paths.decisions, [d.model_dump() for d in decisions])
    updated_findings = apply_decisions(findings, decisions)
    write_json(run_paths.findings, [f.model_dump() for f in updated_findings])

    return run_paths, decisions, verification, updated_findings
