from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple
import subprocess
import tempfile


@dataclass
class ApplyAttempt:
    method: str
    ok: bool
    stdout: str = ""
    stderr: str = ""


@dataclass
class ApplyResult:
    ok: bool
    method: str
    attempts: List[ApplyAttempt]
    # Best-effort list of files targeted by this diff (relative paths).
    files: List[str]
    note: str | None = None


def write_patch(run_dir: Path, diff: str) -> Path:
    patch_path = run_dir / "patches.diff"
    patch_path.write_text(diff, encoding="utf-8")
    return patch_path


def apply_patch(diff: str, cwd: Path) -> ApplyResult:
    files = _extract_target_files(diff)
    unsafe = _first_unsafe_path(files, cwd=cwd)
    if unsafe:
        return ApplyResult(
            ok=False,
            method="blocked",
            attempts=[],
            files=files,
            note=f"Refusing to apply patch with unsafe path: {unsafe}",
        )

    with tempfile.NamedTemporaryFile(mode="w", suffix=".diff", delete=False) as handle:
        handle.write(diff)
        patch_path = Path(handle.name)

    attempts: List[ApplyAttempt] = []

    ok, stdout, stderr = _try_git_apply(patch_path, cwd)
    attempts.append(ApplyAttempt(method="git_apply", ok=ok, stdout=stdout, stderr=stderr))

    if not ok:
        ok, stdout, stderr = _try_patch_apply(patch_path, cwd)
        attempts.append(ApplyAttempt(method="patch", ok=ok, stdout=stdout, stderr=stderr))

    # Many model-generated diffs are "diff-shaped" but malformed (bad @@ ranges, missing prefixes).
    # If system patchers fail, fall back to a strict, context-based applier that ignores ranges.
    if not ok:
        ok, note = _try_loose_apply(diff, cwd=cwd)
        attempts.append(ApplyAttempt(method="loose", ok=ok, stdout=note or "", stderr=""))

    patch_path.unlink(missing_ok=True)
    method = next((a.method for a in attempts if a.ok), "none")
    note = None
    if not ok:
        tail = [a for a in attempts if a.stderr or a.stdout]
        if tail:
            last = tail[-1]
            note = last.stderr or last.stdout

    return ApplyResult(ok=ok, method=method, attempts=attempts, files=files, note=note)


def _try_git_apply(patch_path: Path, cwd: Path) -> Tuple[bool, str, str]:
    try:
        result = subprocess.run(
            # -p1 strips common "a/" and "b/" prefixes.
            ["git", "apply", "-p1", str(patch_path)],
            cwd=cwd,
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,
            timeout=15,
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "git apply timed out"
    except FileNotFoundError:
        return False, "", "git not found"


def _try_patch_apply(patch_path: Path, cwd: Path) -> Tuple[bool, str, str]:
    try:
        result = subprocess.run(
            # -p1 strips the common "a/" and "b/" prefixes; --batch avoids interactive prompts.
            ["patch", "-p1", "--batch", "--forward", "-i", str(patch_path)],
            cwd=cwd,
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,
            timeout=15,
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "patch timed out"
    except FileNotFoundError:
        return False, "", "patch not found"


def _strip_prefix(path: str) -> str:
    p = path.strip()
    if p.startswith(("a/", "b/")):
        return p[2:]
    return p


def _extract_target_files(diff: str) -> List[str]:
    files: List[str] = []
    lines = diff.splitlines()
    for line in lines:
        if not line.startswith(("+++ ", "--- ")):
            continue
        raw = line[4:].strip()
        if raw == "/dev/null":
            continue
        rel = _strip_prefix(raw)
        if rel and rel not in files:
            files.append(rel)
    return files


def _first_unsafe_path(paths: List[str], cwd: Path) -> str | None:
    root = cwd.resolve()
    for p in paths:
        rel = _strip_prefix(p)
        if not rel:
            continue
        if Path(rel).is_absolute():
            return rel
        resolved = (root / rel).resolve()
        try:
            resolved.relative_to(root)
        except Exception:
            return rel
    return None


@dataclass
class FilePatch:
    old_path: str
    new_path: str
    hunks: List[List[str]]


def _parse_file_patches(diff: str) -> List[FilePatch]:
    """
    Parse unified-diff-ish text into file patches.

    We intentionally do NOT rely on @@ ranges being accurate; many model outputs
    have broken counts. We only trust the prefixed hunk lines (' ', '+', '-').
    """
    lines = diff.splitlines()
    patches: List[FilePatch] = []

    i = 0
    while i < len(lines):
        if not lines[i].startswith("--- "):
            i += 1
            continue
        if i + 1 >= len(lines) or not lines[i + 1].startswith("+++ "):
            i += 1
            continue

        old_path = lines[i][4:].strip()
        new_path = lines[i + 1][4:].strip()
        i += 2

        hunks: List[List[str]] = []
        current: List[str] = []
        in_hunk = False

        while i < len(lines) and not lines[i].startswith("--- "):
            line = lines[i]

            if line.startswith("@@"):
                if current:
                    hunks.append(current)
                    current = []
                in_hunk = True
                i += 1
                continue

            if line.startswith((" ", "+", "-", "\\")):
                # If the diff omitted @@, treat the first prefixed block as a hunk.
                if not in_hunk:
                    in_hunk = True
                current.append(line)
                i += 1
                continue

            # Unexpected line inside a file patch; end current hunk if any.
            if current:
                hunks.append(current)
                current = []
            in_hunk = False
            i += 1

        if current:
            hunks.append(current)

        patches.append(FilePatch(old_path=old_path, new_path=new_path, hunks=hunks))

    return patches


def _find_subsequence(haystack: List[str], needle: List[str], start: int = 0) -> int:
    if not needle:
        return start
    limit = len(haystack) - len(needle) + 1
    for i in range(max(start, 0), max(limit, 0)):
        if haystack[i : i + len(needle)] == needle:
            return i
    return -1


def _try_loose_apply(diff: str, cwd: Path) -> Tuple[bool, str]:
    file_patches = _parse_file_patches(diff)
    if not file_patches:
        return False, "No file patches detected in diff"

    root = cwd.resolve()

    for fp in file_patches:
        old_path = _strip_prefix(fp.old_path)
        new_path = _strip_prefix(fp.new_path)

        if new_path == "/dev/null":
            return False, f"Refusing to delete file: {old_path}"

        rel = new_path or old_path
        if not rel:
            return False, "Missing target path in diff"

        target = (root / rel).resolve()
        try:
            target.relative_to(root)
        except Exception:
            return False, f"Unsafe target path: {rel}"

        original = target.read_text(encoding="utf-8", errors="ignore") if target.exists() else ""
        had_trailing_newline = original.endswith("\n") if original else True
        lines = original.splitlines()

        # Apply hunks in order; each hunk is located by matching the "before" block.
        search_from = 0
        for hunk in fp.hunks:
            # Ignore meta lines like "\ No newline at end of file".
            hunk = [l for l in hunk if not l.startswith("\\")]
            before = [l[1:] for l in hunk if l.startswith((" ", "-"))]
            after = [l[1:] for l in hunk if l.startswith((" ", "+"))]

            idx = _find_subsequence(lines, before, start=search_from)
            if idx == -1:
                # Already applied? If the "after" block exists, consider it idempotent.
                already = _find_subsequence(lines, after, start=search_from)
                if already != -1:
                    search_from = already + len(after)
                    continue

                # More forgiving match (rstrip) for minor whitespace drift.
                r_lines = [x.rstrip() for x in lines]
                r_before = [x.rstrip() for x in before]
                idx = _find_subsequence(r_lines, r_before, start=search_from)
                if idx == -1:
                    return False, f"Failed to apply hunk to {rel}: context not found"

            lines = lines[:idx] + after + lines[idx + len(before) :]
            search_from = idx + len(after)

        target.parent.mkdir(parents=True, exist_ok=True)
        text = "\n".join(lines)
        if had_trailing_newline and text and not text.endswith("\n"):
            text += "\n"
        target.write_text(text, encoding="utf-8")

    return True, "Applied via loose matcher"

