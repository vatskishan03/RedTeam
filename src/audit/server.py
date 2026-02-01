from __future__ import annotations

import asyncio
from dataclasses import dataclass
import json
import os
from pathlib import Path
import shutil
import tempfile
import threading
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

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


load_dotenv()

app = FastAPI(title="RedTeam Auditor API", version="0.1.0")


def _parse_cors_origins() -> list[str]:
    # Security: do NOT default to "*" in production. CORS is not auth, but it prevents
    # arbitrary websites from using your backend from a browser context.
    raw = os.getenv("CORS_ORIGINS", "").strip()
    if not raw:
        return ["http://localhost:3000", "http://127.0.0.1:3000"]

    origins = [o.strip() for o in raw.split(",") if o.strip()]
    # Explicitly disallow wildcard configurations.
    return [o for o in origins if o != "*"]


_ALLOWED_ORIGINS = _parse_cors_origins()


app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


SUPPORTED_LANGUAGES = {"python": "py", "javascript": "js", "typescript": "ts"}


class StartAuditRequest(BaseModel):
    code: str = Field(min_length=1, max_length=250_000)
    language: str = Field(default="python")
    heuristic: bool = Field(default=False)
    max_rounds: Optional[int] = Field(default=None, ge=1, le=10)


class StartAuditResponse(BaseModel):
    run_id: str
    stream_url: str


@dataclass
class AuditJob:
    run_id: str
    run_dir: Path
    temp_dir: Path
    loop: asyncio.AbstractEventLoop
    queue: "asyncio.Queue[dict]"


_jobs: Dict[str, AuditJob] = {}
_jobs_lock = threading.Lock()


@app.middleware("http")
async def enforce_origin(request: Request, call_next):
    # Protect the backend from being driven by arbitrary websites.
    # Note: this is still not full authentication (anyone can spoof headers),
    # but it removes "open to the entire web" behavior for browser clients.
    if request.method == "OPTIONS":
        return await call_next(request)

    path = request.url.path
    if path in {"/healthz", "/docs", "/openapi.json"} or path.startswith("/docs/"):
        return await call_next(request)

    origin = request.headers.get("origin")
    if not origin:
        return JSONResponse({"detail": "Missing Origin header."}, status_code=403)
    if origin not in _ALLOWED_ORIGINS:
        return JSONResponse({"detail": f"Origin not allowed: {origin}"}, status_code=403)

    return await call_next(request)


@app.get("/healthz")
def healthz() -> JSONResponse:
    return JSONResponse({"ok": True})


@app.post("/audit/start", response_model=StartAuditResponse)
async def start_audit(req: StartAuditRequest) -> StartAuditResponse:
    language = (req.language or "python").lower().strip()
    if language not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=400, detail=f"Unsupported language: {language}")

    run_paths = ensure_run_dir(None)
    run_id = run_paths.root.name

    temp_root = Path(tempfile.mkdtemp(prefix="redteam-"))
    ext = SUPPORTED_LANGUAGES[language]
    (temp_root / f"snippet.{ext}").write_text(req.code, encoding="utf-8")

    job = AuditJob(
        run_id=run_id,
        run_dir=run_paths.root,
        temp_dir=temp_root,
        loop=asyncio.get_running_loop(),
        queue=asyncio.Queue(),
    )

    with _jobs_lock:
        _jobs[run_id] = job

    max_rounds = int(req.max_rounds or int(os.getenv("AUDIT_MAX_ROUNDS", "6")))

    thread = threading.Thread(
        target=_run_job_thread,
        args=(job, max_rounds, req.heuristic),
        daemon=True,
    )
    thread.start()

    return StartAuditResponse(run_id=run_id, stream_url=f"/audit/stream/{run_id}")


@app.get("/audit/stream/{run_id}")
async def stream_audit(run_id: str) -> StreamingResponse:
    with _jobs_lock:
        job = _jobs.get(run_id)

    if job is None:
        raise HTTPException(status_code=404, detail="Unknown run_id")

    async def event_stream():
        try:
            while True:
                payload = await job.queue.get()
                yield f"data: {json.dumps(payload)}\n\n"
                if payload.get("type") in {"done", "error"}:
                    break
        finally:
            # Cleanup temp dir and job record once the client is done streaming.
            try:
                shutil.rmtree(job.temp_dir, ignore_errors=True)
            except Exception:
                pass
            with _jobs_lock:
                _jobs.pop(run_id, None)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


def _emit(job: AuditJob, payload: dict) -> None:
    payload = dict(payload)
    payload.setdefault("run_id", job.run_id)

    def _put():
        try:
            job.queue.put_nowait(payload)
        except Exception:
            # Client disconnected or loop closing; drop events.
            pass

    try:
        job.loop.call_soon_threadsafe(_put)
    except Exception:
        pass


def _timeline(job: AuditJob, step: str, status: str) -> None:
    _emit(job, {"type": "timeline_update", "step": step, "status": status})


def _agent_start(job: AuditJob, agent: str) -> None:
    _emit(job, {"type": "agent_start", "agent": agent})


def _agent_complete(job: AuditJob, agent: str) -> None:
    _emit(job, {"type": "agent_complete", "agent": agent})


def _agent_message(job: AuditJob, agent: str, content: str, message_type: str = "text") -> None:
    _emit(
        job,
        {"type": "agent_message", "agent": agent, "content": content, "messageType": message_type},
    )


def _status_update(job: AuditJob, status: str) -> None:
    _emit(job, {"type": "status_update", "status": status})


def _verdict_event(job: AuditJob, verdict: str, counts: dict | None = None) -> None:
    payload: dict[str, Any] = {"type": "verdict", "verdict": verdict}
    if counts:
        payload["counts"] = counts
    _emit(job, payload)


def _report_event(job: AuditJob, content: str) -> None:
    _emit(job, {"type": "report", "content": content})


def _format_finding(finding: Finding) -> str:
    return (
        f"⚠️ {finding.severity.upper()}: {finding.title}\n"
        f"CWE: {finding.cwe}\n"
        f"Location: {finding.file}:{finding.line}\n"
        f"Evidence: {finding.evidence}\n"
        f"Impact: {finding.impact}\n"
        f"Fix plan: {finding.fix_plan}"
    )


def _format_patch(patch: Patch) -> str:
    diff = patch.diff.strip()
    if len(diff) > 1200:
        diff = diff[:1200] + "\n..."
    return f"🔧 Patch for {patch.id}\nRationale: {patch.rationale}\n\n```diff\n{diff}\n```"


def _format_decisions(decisions: list[Decision]) -> str:
    lines = ["⚖️ Arbiter verdicts:"]
    for d in decisions:
        lines.append(f"- {d.id}: {d.status.upper()} ({d.reason})")
    return "\n".join(lines)


def _calculate_verdict(decisions: list[Decision]) -> str:
    if not decisions:
        return "rejected"
    fixed = len([d for d in decisions if d.status == "fixed"])
    rejected = len([d for d in decisions if d.status == "rejected"])
    if fixed and rejected:
        return "partial"
    return "approved" if fixed else "rejected"


def _run_job_thread(job: AuditJob, max_rounds: int, force_heuristic: bool) -> None:
    client = OpenAIClient()
    use_heuristics = bool(force_heuristic) or not getattr(client, "available", False)

    try:
        _status_update(job, "scanning")
        _timeline(job, "scan", "active")
        _agent_start(job, "attacker")
        _agent_message(job, "attacker", "Initializing scan...", "text")

        run_paths, findings, _ = run_scan(
            job.temp_dir, client, run_id=job.run_id, use_heuristics=use_heuristics
        )
        meta = read_json(run_paths.meta, default={})
        if isinstance(meta, dict) and str(meta.get("mode", "")).startswith("heuristic"):
            use_heuristics = True
        if isinstance(meta, dict) and meta.get("mode"):
            _agent_message(job, "attacker", f"Scan mode: {meta['mode']}", "text")
        if isinstance(meta, dict) and meta.get("llm_error"):
            _agent_message(job, "attacker", f"LLM error: {meta['llm_error']}", "text")
        _agent_message(job, "attacker", f"Run ID: {job.run_id}", "text")

        _timeline(job, "scan", "complete")
        _timeline(job, "vulns", "active")

        if not findings:
            _agent_message(job, "attacker", "No vulnerabilities detected.", "text")
        else:
            for f in findings:
                _agent_message(job, "attacker", _format_finding(f), "vulnerability")

        _agent_complete(job, "attacker")
        _timeline(job, "vulns", "complete")

        baseline_findings = None
        if getattr(client, "available", False) and not use_heuristics:
            try:
                baseline_findings = run_baseline(job.temp_dir, client, run_id=job.run_id)
            except Exception:
                baseline_findings = None

        updated = findings
        decisions: list[Decision] = []
        verification: list[VerificationResult] = []
        verdict = "rejected"

        for round_idx in range(1, max_rounds + 1):
            _status_update(job, "proposing_fixes")
            _timeline(job, "fix", "active")
            _agent_start(job, "defender")
            _agent_message(job, "defender", f"Round {round_idx}/{max_rounds}: proposing patches...", "text")

            _, _, patches = run_fix(
                job.temp_dir,
                client,
                run_id=job.run_id,
                autofix=True,
                use_heuristics=use_heuristics,
            )

            if not patches:
                _agent_message(job, "defender", "No patches generated (no active findings).", "text")
            else:
                for p in patches:
                    _agent_message(job, "defender", _format_patch(p), "fix")

            _agent_complete(job, "defender")
            _timeline(job, "fix", "complete")

            _status_update(job, "re_attacking")
            _timeline(job, "reattack", "active")
            _agent_start(job, "attacker")
            _agent_message(job, "attacker", f"Round {round_idx}/{max_rounds}: re-attacking...", "text")

            _, decisions, verification, updated = run_verify(
                job.temp_dir,
                client,
                run_id=job.run_id,
                reattack=True,
                use_heuristics=use_heuristics,
            )
            reattack_payload = read_json(run_paths.reattack, default=[])
            reattack_findings = [Finding.model_validate(item) for item in reattack_payload] if reattack_payload else []

            if not reattack_findings:
                _agent_message(job, "attacker", "No issues found on re-attack.", "text")
            else:
                for f in reattack_findings:
                    _agent_message(job, "attacker", _format_finding(f), "vulnerability")

            _agent_complete(job, "attacker")
            _timeline(job, "reattack", "complete")

            _status_update(job, "validating")
            _timeline(job, "verdict", "active")
            _agent_start(job, "arbiter")
            _agent_message(job, "arbiter", "Reviewing verification results...", "text")
            _agent_message(job, "arbiter", _format_decisions(decisions), "verdict")

            verdict = _calculate_verdict(decisions)
            fixed = len([d for d in decisions if d.status == "fixed"])
            rejected = len([d for d in decisions if d.status == "rejected"])
            _verdict_event(job, verdict, counts={"total": len(decisions), "fixed": fixed, "rejected": rejected})

            if verdict != "approved":
                if round_idx < max_rounds:
                    _agent_message(job, "arbiter", f"Not approved after round {round_idx}. Continuing...", "text")
                else:
                    _agent_message(job, "arbiter", f"Max rounds reached ({max_rounds}).", "text")

            _agent_complete(job, "arbiter")
            _timeline(job, "verdict", "complete")

            if verdict == "approved":
                break

        _status_update(job, "generating_report")
        _timeline(job, "report", "active")
        _agent_start(job, "reporter")
        _agent_message(job, "reporter", "Generating security report...", "text")

        build_scorecard(run_paths, updated, decisions, verification, baseline=baseline_findings)
        run_report(job.temp_dir, client, run_id=job.run_id, use_heuristics=use_heuristics)

        report_content = run_paths.report.read_text(encoding="utf-8")
        _report_event(job, report_content)

        _agent_complete(job, "reporter")
        _timeline(job, "report", "complete")

        _emit(job, {"type": "done"})
    except Exception as exc:
        _emit(job, {"type": "error", "message": f"Audit failed: {exc}"})
