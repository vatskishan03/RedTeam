from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List
import json
import subprocess


@dataclass
class ToolResult:
    name: str
    command: List[str]
    exit_code: int
    stdout: str
    stderr: str
    parsed: dict | None = None


def run_command(command: List[str], cwd: Path) -> ToolResult:
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
        )
        return ToolResult(
            name=command[0],
            command=command,
            exit_code=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
        )
    except FileNotFoundError as exc:
        return ToolResult(
            name=command[0],
            command=command,
            exit_code=127,
            stdout="",
            stderr=str(exc),
        )


def _cwd(target: Path) -> Path:
    return target if target.is_dir() else target.parent


def run_bandit(target: Path) -> ToolResult:
    command = ["bandit", "-r", str(target), "-f", "json"]
    result = run_command(command, cwd=_cwd(target))
    try:
        result.parsed = json.loads(result.stdout)
    except json.JSONDecodeError:
        result.parsed = None
    return result


def summarize_bandit(result: ToolResult, limit: int = 20) -> str:
    if not result.parsed or "results" not in result.parsed:
        return ""
    lines = ["# Static analysis hints (bandit)"]
    for item in result.parsed.get("results", [])[:limit]:
        filename = item.get("filename", "")
        line = item.get("line_number", "")
        test_id = item.get("test_id", "")
        issue = item.get("issue_text", "")
        lines.append(f"- {test_id} {filename}:{line} {issue}")
    return "\n".join(lines)


def run_ruff(target: Path) -> ToolResult:
    command = ["ruff", "check", str(target), "--output-format", "json"]
    result = run_command(command, cwd=_cwd(target))
    try:
        result.parsed = json.loads(result.stdout)
    except json.JSONDecodeError:
        result.parsed = None
    return result


def run_pytest(target: Path) -> ToolResult:
    has_tests = any(
        path.name.startswith("test_") or path.name.endswith("_test.py")
        for path in target.rglob("*.py")
    )
    if not has_tests:
        return ToolResult(
            name="pytest",
            command=["pytest", "-q", str(target)],
            exit_code=0,
            stdout="No tests found. Skipping.",
            stderr="",
        )
    command = ["pytest", "-q", str(target)]
    return run_command(command, cwd=_cwd(target))
