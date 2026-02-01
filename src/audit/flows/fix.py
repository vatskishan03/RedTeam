from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from audit.agents import BlueTeamAgent
from audit.contracts import Finding, Patch
from audit.flows.scan import run_scan
from audit.flows.utils import normalize_patches
from audit.tools.jsonio import read_json, write_json
from audit.tools.patch import ApplyResult, apply_patch
from audit.tools.heuristic_patches import generate_heuristic_patches
from audit.tools.run_state import RunPaths, ensure_run_dir
from audit.tools.files import build_code_context, list_code_files
from audit.config import settings


def _load_findings(run_paths: RunPaths) -> List[Finding]:
    payload = read_json(run_paths.findings, default=[])
    return [Finding.model_validate(item) for item in payload]


def run_fix(
    target_path: Path,
    client,
    run_id: str | None = None,
    autofix: bool = False,
    use_heuristics: bool = False,
) -> Tuple[RunPaths, List[Finding], List[Patch]]:
    run_paths = ensure_run_dir(run_id)
    findings = _load_findings(run_paths)
    if not findings:
        run_paths, findings, _ = run_scan(
            target_path, client, run_id=run_paths.root.name, use_heuristics=use_heuristics
        )

    active_findings = [f for f in findings if f.status != "fixed"]
    if not active_findings:
        write_json(run_paths.patches, [])
        write_json(run_paths.apply, [])
        return run_paths, findings, []

    files = list_code_files(target_path)
    code_context = build_code_context(
        files, settings.max_file_bytes, settings.max_total_bytes
    )

    # Feedback from previous round (if any). This is what makes the loop truly adversarial:
    # the defender gets the arbiter's rejection reasons + attacker re-attack evidence.
    feedback = {
        "decisions": read_json(run_paths.decisions, default=[]),
        "reattack": read_json(run_paths.reattack, default=[]),
        "apply_results": read_json(run_paths.apply, default=[]),
    }

    patches: List[Patch] = []
    if getattr(client, "available", False) and not use_heuristics:
        try:
            agent = BlueTeamAgent(client)
            patches = agent.run(code_context, active_findings, feedback=feedback)
            patches = normalize_patches(patches, active_findings)
        except Exception:
            patches = []

    # If the defender doesn't cover all active findings, ask again for the missing ones
    # (common failure mode: a single diff fixes multiple issues but is only labeled with one id).
    covered = {p.id for p in patches}
    missing = [f for f in active_findings if f.id not in covered]
    if missing and getattr(client, "available", False) and not use_heuristics:
        try:
            agent = BlueTeamAgent(client)
            extra_feedback = {
                **feedback,
                "missing_finding_ids": [f.id for f in missing],
                "instruction": "Return a Patch entry for EVERY missing finding id.",
            }
            more = agent.run(code_context, missing, feedback=extra_feedback)
            more = normalize_patches(more, missing)
            patches.extend(more)
        except Exception:
            pass

    covered = {p.id for p in patches}
    missing = [f for f in active_findings if f.id not in covered]
    if missing or not patches:
        root = target_path if target_path.is_dir() else target_path.parent
        patches.extend(generate_heuristic_patches(missing or active_findings, root))

    write_json(run_paths.patches, [p.model_dump() for p in patches])

    apply_results = []
    if autofix and patches:
        cwd = target_path if target_path.is_dir() else target_path.parent
        # Apply per-patch so we can attribute failures and keep the loop informative.
        applied_by_diff: dict[str, ApplyResult] = {}
        for patch in patches:
            key = patch.diff.strip()
            cached = applied_by_diff.get(key)
            if cached is None:
                cached = apply_patch(patch.diff, cwd=cwd)
                applied_by_diff[key] = cached
            result = cached
            apply_results.append(
                {
                    "id": patch.id,
                    "ok": result.ok,
                    "method": result.method,
                    "files": result.files,
                    "note": result.note,
                    "attempts": [a.__dict__ for a in result.attempts],
                }
            )

    write_json(run_paths.apply, apply_results)

    return run_paths, findings, patches
