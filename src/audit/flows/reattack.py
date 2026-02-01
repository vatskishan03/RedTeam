from __future__ import annotations

from pathlib import Path
from typing import List

from audit.agents import RedTeamAgent
from audit.contracts import Finding
from audit.tools.files import build_code_context, list_code_files
from audit.tools.heuristics import scan_file
from audit.tools.files import read_file
from audit.tools.jsonio import write_json
from audit.tools.run_state import ensure_run_dir
from audit.tools.linters import run_bandit, summarize_bandit
from audit.flows.utils import normalize_findings
from audit.config import settings


def run_reattack(
    target_path: Path,
    client,
    run_id: str | None = None,
    use_heuristics: bool = False,
) -> List[Finding]:
    run_paths = ensure_run_dir(run_id)
    files = list_code_files(target_path)
    if not files:
        return []
    code_context = build_code_context(
        files, settings.max_file_bytes, settings.max_total_bytes
    )
    if getattr(client, "available", False) and not use_heuristics:
        bandit_result = run_bandit(target_path)
        hints = summarize_bandit(bandit_result)
        if hints:
            code_context = f"{code_context}\n\n{hints}"

    findings: List[Finding] = []
    if getattr(client, "available", False) and not use_heuristics:
        try:
            agent = RedTeamAgent(client)
            findings = agent.run(code_context, max_findings=8)
        except Exception:
            findings = []
    else:
        payload = []
        counter = 1
        for path in files:
            text = read_file(path, settings.max_file_bytes)
            for item in scan_file(path, text):
                payload.append(
                    {
                        "id": f"F-{counter:03d}",
                        "title": item.title,
                        "cwe": item.cwe,
                        "severity": item.severity,
                        "file": item.file,
                        "line": item.line,
                        "evidence": item.evidence,
                        "impact": item.impact,
                        "fix_plan": item.fix_plan,
                        "status": "open",
                    }
                )
                counter += 1
        findings = RedTeamAgent.from_heuristics(payload)

    findings = normalize_findings(findings)
    write_json(run_paths.reattack, [f.model_dump() for f in findings])
    return findings
