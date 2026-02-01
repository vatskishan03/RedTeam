from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from audit.agents import BlueTeamAgent
from audit.contracts import Finding, Patch
from audit.flows.scan import run_scan
from audit.flows.utils import normalize_patches
from audit.tools.jsonio import read_json, write_json
from audit.tools.patch import apply_patch
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

    if not patches:
        patches = generate_heuristic_patches(
            active_findings, target_path if target_path.is_dir() else target_path.parent
        )

    write_json(run_paths.patches, [p.model_dump() for p in patches])

    apply_results = []
    if autofix and patches:
        cwd = target_path if target_path.is_dir() else target_path.parent
        # Apply per-patch so we can attribute failures and keep the loop informative.
        for patch in patches:
            result = apply_patch(patch.diff, cwd=cwd)
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
