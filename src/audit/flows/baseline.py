from __future__ import annotations

from pathlib import Path
from typing import List

from audit.agents import RedTeamAgent
from audit.contracts import Finding
from audit.tools.files import build_code_context, list_code_files
from audit.tools.jsonio import write_json
from audit.tools.run_state import RunPaths, ensure_run_dir
from audit.flows.utils import normalize_findings
from audit.config import settings


def run_baseline(
    target_path: Path,
    client,
    run_id: str | None = None,
) -> List[Finding]:
    run_paths = ensure_run_dir(run_id)
    files = list_code_files(target_path)
    if not files:
        return []
    code_context = build_code_context(
        files, settings.max_file_bytes, settings.max_total_bytes
    )

    findings: List[Finding] = []
    if getattr(client, "available", False):
        try:
            agent = RedTeamAgent(client)
            findings = agent.run(code_context, max_findings=6)
        except Exception:
            findings = []
    else:
        findings = []

    findings = normalize_findings(findings)
    write_json(run_paths.baseline, [f.model_dump() for f in findings])
    return findings
