from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from audit.agents import RedTeamAgent
from audit.contracts import Finding
from audit.tools.files import build_code_context, list_code_files, read_file
from audit.tools.heuristics import scan_file
from audit.tools.jsonio import write_json
from audit.tools.run_state import RunPaths, ensure_run_dir, write_meta
from audit.tools.linters import run_bandit, summarize_bandit
from audit.flows.utils import normalize_findings
from audit.config import settings


def run_scan(
    target_path: Path,
    client,
    run_id: str | None = None,
    use_heuristics: bool = False,
) -> Tuple[RunPaths, List[Finding], str]:
    run_paths = ensure_run_dir(run_id)
    files = list_code_files(target_path)
    if not files:
        raise ValueError(f"No supported files found in {target_path}")
    code_context = build_code_context(
        files, settings.max_file_bytes, settings.max_total_bytes
    )
    if getattr(client, "available", False) and not use_heuristics:
        bandit_result = run_bandit(target_path)
        hints = summarize_bandit(bandit_result)
        if hints:
            code_context = f"{code_context}\n\n{hints}"
    run_paths.context.write_text(code_context, encoding="utf-8")

    findings: List[Finding] = []
    mode = "llm"
    if use_heuristics or not getattr(client, "available", False):
        mode = "heuristic"
        findings = _run_heuristics(files)
    else:
        try:
            agent = RedTeamAgent(client)
            findings = agent.run(code_context)
        except Exception:
            mode = "heuristic-fallback"
            findings = _run_heuristics(files)

    findings = normalize_findings(findings)
    write_json(run_paths.findings, [f.model_dump() for f in findings])
    write_meta(run_paths, target_path, settings.model, mode)
    return run_paths, findings, code_context


def _run_heuristics(files: list[Path]) -> List[Finding]:
    heuristic_payload = []
    counter = 1
    for path in files:
        text = read_file(path, settings.max_file_bytes)
        for item in scan_file(path, text):
            heuristic_payload.append(
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
    return RedTeamAgent.from_heuristics(heuristic_payload)
