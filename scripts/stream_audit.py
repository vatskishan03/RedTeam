#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
import shutil
from typing import List

from dotenv import load_dotenv

from audit.config import settings
from audit.contracts import Decision, Finding, Patch, VerificationResult
from audit.flows.baseline import run_baseline
from audit.flows.fix import run_fix
from audit.flows.report import run_report
from audit.flows.scan import run_scan
from audit.flows.scorecard import build_scorecard
from audit.flows.verify import run_verify
from audit.tools.jsonio import read_json
from audit.tools.openai_client import OpenAIClient
from audit.tools.run_state import ensure_run_dir


RUN_ID: str | None = None


def emit(payload: dict) -> None:
    try:
        if RUN_ID and "run_id" not in payload:
            payload["run_id"] = RUN_ID
        sys.stdout.write(json.dumps(payload) + "\n")
        sys.stdout.flush()
    except BrokenPipeError:
        raise SystemExit(0)


def timeline(step: str, status: str) -> None:
    emit({"type": "timeline_update", "step": step, "status": status})


def agent_start(agent: str) -> None:
    emit({"type": "agent_start", "agent": agent})


def agent_complete(agent: str) -> None:
    emit({"type": "agent_complete", "agent": agent})


def agent_message(agent: str, content: str, message_type: str = "text") -> None:
    emit(
        {
            "type": "agent_message",
            "agent": agent,
            "content": content,
            "messageType": message_type,
        }
    )


def status_update(status: str) -> None:
    emit({"type": "status_update", "status": status})


def verdict_event(verdict: str, counts: dict | None = None) -> None:
    payload = {"type": "verdict", "verdict": verdict}
    if counts:
        payload["counts"] = counts
    emit(payload)


def report_event(content: str) -> None:
    emit({"type": "report", "content": content})


def format_finding(finding: Finding) -> str:
    return (
        f"⚠️ {finding.severity.upper()}: {finding.title}\n"
        f"CWE: {finding.cwe}\n"
        f"Location: {finding.file}:{finding.line}\n"
        f"Evidence: {finding.evidence}\n"
        f"Impact: {finding.impact}\n"
        f"Fix plan: {finding.fix_plan}"
    )


def format_patch(patch: Patch) -> str:
    diff = patch.diff.strip()
    if len(diff) > 1200:
        diff = diff[:1200] + "\n..."
    return f"🔧 Patch for {patch.id}\nRationale: {patch.rationale}\n\n```diff\n{diff}\n```"


def format_decisions(decisions: List[Decision]) -> str:
    lines = ["⚖️ Arbiter verdicts:"]
    for decision in decisions:
        lines.append(f"- {decision.id}: {decision.status.upper()} ({decision.reason})")
    return "\n".join(lines)


def calculate_verdict(decisions: List[Decision]) -> str:
    if not decisions:
        return "rejected"
    fixed = len([d for d in decisions if d.status == "fixed"])
    rejected = len([d for d in decisions if d.status == "rejected"])
    if fixed and rejected:
        return "partial"
    return "approved" if fixed else "rejected"


def load_reattack(run_dir: Path) -> List[Finding]:
    payload = read_json(run_dir / "reattack.json", default=[])
    return [Finding.model_validate(item) for item in payload]


def load_apply_results(run_dir: Path) -> list[dict]:
    payload = read_json(run_dir / "apply.json", default=[])
    return payload if isinstance(payload, list) else []


def format_apply_results(apply_results: list[dict]) -> str:
    if not apply_results:
        return "No patch application results recorded."
    lines = ["🧩 Patch application results:"]
    for item in apply_results:
        fid = item.get("id", "?")
        ok = item.get("ok", False)
        method = item.get("method", "none")
        note = item.get("note")
        suffix = f" ({note})" if note else ""
        lines.append(f"- {fid}: {'OK' if ok else 'FAIL'} via {method}{suffix}")
    return "\n".join(lines)


def snapshot_round(run_dir: Path, round_idx: int) -> None:
    """
    Persist per-round artifacts for debugging. The core flows overwrite files each round,
    so we copy them into runs/<run_id>/rounds/<n>/... to make iteration auditable.
    """
    src_files = [
        "findings.json",
        "patches.json",
        "apply.json",
        "reattack.json",
        "verification.json",
        "decisions.json",
    ]
    dest = run_dir / "rounds" / f"round_{round_idx:02d}"
    dest.mkdir(parents=True, exist_ok=True)
    for name in src_files:
        src = run_dir / name
        if src.exists():
            shutil.copyfile(src, dest / name)


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", required=True, help="Path to codebase")
    parser.add_argument("--heuristic", action="store_true")
    parser.add_argument(
        "--max-rounds",
        type=int,
        default=int(os.getenv("AUDIT_MAX_ROUNDS", "6")),
        help="Max adversarial fix/re-attack rounds (default: AUDIT_MAX_ROUNDS or 6).",
    )
    args = parser.parse_args()

    target_path = Path(args.path)
    client = OpenAIClient()
    use_heuristics = args.heuristic or not client.available
    max_rounds = max(1, int(args.max_rounds))

    global RUN_ID
    run_paths = ensure_run_dir(None)
    RUN_ID = run_paths.root.name

    try:
        status_update("scanning")
        timeline("scan", "active")
        agent_start("attacker")
        agent_message("attacker", "Initializing scan...", "text")

        run_paths, findings, _ = run_scan(
            target_path, client, run_id=run_paths.root.name, use_heuristics=use_heuristics
        )
        meta = read_json(run_paths.meta, default={})
        if isinstance(meta, dict) and str(meta.get("mode", "")).startswith("heuristic"):
            use_heuristics = True
        if isinstance(meta, dict) and meta.get("mode"):
            agent_message("attacker", f"Scan mode: {meta['mode']}", "text")
        if isinstance(meta, dict) and meta.get("llm_error"):
            agent_message("attacker", f"LLM error: {meta['llm_error']}", "text")
        agent_message("attacker", f"Run ID: {run_paths.root.name}", "text")

        timeline("scan", "complete")
        timeline("vulns", "active")

        if not findings:
            agent_message("attacker", "No vulnerabilities detected.", "text")
        else:
            for finding in findings:
                agent_message("attacker", format_finding(finding), "vulnerability")

        agent_complete("attacker")
        timeline("vulns", "complete")

        # Baseline scan: compare single-agent attacker findings before any fixes.
        baseline_findings = None
        if getattr(client, "available", False) and not use_heuristics:
            try:
                baseline_findings = run_baseline(
                    target_path, client, run_id=run_paths.root.name
                )
            except Exception:
                baseline_findings = None

        updated = findings
        decisions: List[Decision] = []
        verification: List[VerificationResult] = []
        verdict = "rejected"

        for round_idx in range(1, max_rounds + 1):
            status_update("proposing_fixes")
            timeline("fix", "active")
            agent_start("defender")
            agent_message(
                "defender",
                f"Round {round_idx}/{max_rounds}: proposing minimal patches...",
                "text",
            )

            _, _, patches = run_fix(
                target_path,
                client,
                run_id=run_paths.root.name,
                autofix=True,
                use_heuristics=use_heuristics,
            )
            apply_results = load_apply_results(run_paths.root)

            if not patches:
                agent_message(
                    "defender",
                    "No patches generated (LLM unavailable or no active findings).",
                    "text",
                )
            else:
                for patch in patches:
                    agent_message("defender", format_patch(patch), "fix")
                agent_message("defender", format_apply_results(apply_results), "text")

            agent_complete("defender")
            timeline("fix", "complete")

            status_update("re_attacking")
            timeline("reattack", "active")
            agent_start("attacker")
            agent_message(
                "attacker",
                f"Round {round_idx}/{max_rounds}: re-attacking the patched code...",
                "text",
            )

            _, decisions, verification, updated = run_verify(
                target_path,
                client,
                run_id=run_paths.root.name,
                reattack=True,
                use_heuristics=use_heuristics,
            )
            reattack_findings = load_reattack(run_paths.root)
            snapshot_round(run_paths.root, round_idx)

            if not reattack_findings:
                agent_message("attacker", "No issues found on re-attack.", "text")
            else:
                for finding in reattack_findings:
                    agent_message("attacker", format_finding(finding), "vulnerability")

            agent_complete("attacker")
            timeline("reattack", "complete")

            status_update("validating")
            timeline("verdict", "active")
            agent_start("arbiter")
            agent_message("arbiter", "Reviewing verification results...", "text")
            agent_message("arbiter", format_decisions(decisions), "verdict")
            verdict = calculate_verdict(decisions)
            fixed = len([d for d in decisions if d.status == "fixed"])
            rejected = len([d for d in decisions if d.status == "rejected"])
            verdict_event(
                verdict,
                counts={"total": len(decisions), "fixed": fixed, "rejected": rejected},
            )
            if verdict != "approved":
                if round_idx < max_rounds:
                    agent_message(
                        "arbiter",
                        f"Not approved after round {round_idx}. Continuing adversarial loop...",
                        "text",
                    )
                else:
                    agent_message(
                        "arbiter",
                        f"Max rounds ({max_rounds}) reached. Proceeding to report with verdict: {verdict}.",
                        "text",
                    )
            agent_complete("arbiter")
            timeline("verdict", "complete")

            if verdict == "approved":
                break

        status_update("generating_report")
        timeline("report", "active")
        agent_start("reporter")
        agent_message("reporter", "Generating security report...", "text")

        build_scorecard(
            run_paths,
            updated,
            decisions,
            verification,
            baseline=baseline_findings,
        )
        run_report(
            target_path, client, run_id=run_paths.root.name, use_heuristics=use_heuristics
        )

        report_path = run_paths.report
        report_content = report_path.read_text(encoding="utf-8")
        report_event(report_content)
        agent_complete("reporter")
        timeline("report", "complete")

        emit({"type": "done"})
        return 0
    except Exception as exc:
        emit({"type": "error", "message": f"Audit failed: {exc}"})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
