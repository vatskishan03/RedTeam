from __future__ import annotations

from pathlib import Path
from typing import Iterable, List
import os

IGNORE_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    "runs",
    "dist",
    "build",
    "node_modules",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}


def _default_extensions() -> List[str]:
    env_value = os.getenv("AUDIT_EXTENSIONS")
    if env_value:
        return [ext.strip() for ext in env_value.split(",") if ext.strip()]
    return [".py", ".js", ".ts", ".jsx", ".tsx"]


def list_code_files(root: Path, extensions: Iterable[str] | None = None) -> List[Path]:
    extensions = list(extensions or _default_extensions())
    if root.is_file():
        return [root] if root.suffix in extensions else []
    files: List[Path] = []
    for path in root.rglob("*"):
        if path.is_dir() and path.name in IGNORE_DIRS:
            continue
        if path.is_file() and path.suffix in extensions:
            if any(part in IGNORE_DIRS for part in path.parts):
                continue
            files.append(path)
    return sorted(files)


def read_file(path: Path, max_bytes: int) -> str:
    raw = path.read_bytes()[:max_bytes]
    return raw.decode("utf-8", errors="ignore")


def build_code_context(paths: Iterable[Path], max_file_bytes: int, max_total_bytes: int) -> str:
    sections = []
    total = 0
    for path in paths:
        text = read_file(path, max_file_bytes)
        total += len(text.encode("utf-8"))
        if total > max_total_bytes:
            break
        numbered = "\n".join(
            f"{idx:04d} {line}"
            for idx, line in enumerate(text.splitlines(), start=1)
        )
        sections.append(f"# File: {path}\n{numbered}")
    return "\n\n".join(sections)
