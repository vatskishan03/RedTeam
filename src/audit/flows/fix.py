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

    files = list_code_files(target_path)
    code_context = build_code_context(
        files, settings.max_file_bytes, settings.max_total_bytes
    )

    patches: List[Patch] = []
    if getattr(client, "available", False) and not use_heuristics:
        try:
            agent = BlueTeamAgent(client)
            patches = agent.run(code_context, findings)
            patches = normalize_patches(patches, findings)
        except Exception:
            patches = []

    if not patches:
        patches = generate_heuristic_patches(findings, target_path if target_path.is_dir() else target_path.parent)

    write_json(run_paths.patches, [p.model_dump() for p in patches])

    if autofix and patches:
        combined = "\n".join(p.diff for p in patches)
        cwd = target_path if target_path.is_dir() else target_path.parent
        apply_patch(combined, cwd=cwd)

    return run_paths, findings, patches
