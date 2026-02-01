from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional
import uuid
import json

from audit.config import settings


@dataclass(frozen=True)
class RunPaths:
    root: Path
    context: Path
    findings: Path
    patches: Path
    verification: Path
    decisions: Path
    report: Path
    meta: Path


def create_run_id() -> str:
    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    suffix = uuid.uuid4().hex[:8]
    return f"{stamp}_{suffix}"


def ensure_run_dir(run_id: Optional[str] = None) -> RunPaths:
    run_id = run_id or create_run_id()
    root = settings.run_dir / run_id
    root.mkdir(parents=True, exist_ok=True)
    return RunPaths(
        root=root,
        context=root / "context.txt",
        findings=root / "findings.json",
        patches=root / "patches.json",
        verification=root / "verification.json",
        decisions=root / "decisions.json",
        report=root / "REPORT.md",
        meta=root / "meta.json",
    )


def write_meta(run_paths: RunPaths, target_path: Path, model: str, mode: str) -> None:
    payload = {
        "run_id": run_paths.root.name,
        "created_at": datetime.utcnow().isoformat(),
        "target_path": str(target_path),
        "model": model,
        "mode": mode,
    }
    run_paths.meta.write_text(json.dumps(payload, indent=2), encoding="utf-8")
