from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile


def write_patch(run_dir: Path, diff: str) -> Path:
    patch_path = run_dir / "patches.diff"
    patch_path.write_text(diff, encoding="utf-8")
    return patch_path


def apply_patch(diff: str, cwd: Path) -> bool:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".diff", delete=False) as handle:
        handle.write(diff)
        patch_path = Path(handle.name)

    success = _try_git_apply(patch_path, cwd) or _try_patch_apply(patch_path, cwd)
    patch_path.unlink(missing_ok=True)
    return success


def _try_git_apply(patch_path: Path, cwd: Path) -> bool:
    try:
        result = subprocess.run(
            ["git", "apply", str(patch_path)],
            cwd=cwd,
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def _try_patch_apply(patch_path: Path, cwd: Path) -> bool:
    try:
        result = subprocess.run(
            ["patch", "-p0", "-i", str(patch_path)],
            cwd=cwd,
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False
