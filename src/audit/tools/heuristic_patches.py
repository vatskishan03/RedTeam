from __future__ import annotations

from dataclasses import dataclass
from difflib import unified_diff
from pathlib import Path
import re
from typing import List, Optional

from audit.contracts import Finding, Patch


@dataclass
class PatchCandidate:
    diff: str
    rationale: str


def generate_heuristic_patches(findings: List[Finding], root: Path) -> List[Patch]:
    patches: List[Patch] = []
    for finding in findings:
        patch = _patch_for_finding(finding, root)
        if patch:
            patches.append(Patch(id=finding.id, diff=patch.diff, rationale=patch.rationale))
    return patches


def _patch_for_finding(finding: Finding, root: Path) -> Optional[PatchCandidate]:
    file_path = Path(finding.file)
    if not file_path.exists():
        return None
    try:
        original_text = file_path.read_text(encoding="utf-8")
    except Exception:
        return None

    lines = original_text.splitlines()
    new_lines = list(lines)
    changed = False

    title = finding.title.lower()
    cwe = finding.cwe.upper()

    if cwe == "CWE-89" or "sql injection" in title:
        changed = _fix_sql_injection(new_lines, finding)
    elif cwe == "CWE-20" and "yaml" in title:
        changed = _simple_replace(new_lines, "yaml.load", "yaml.safe_load")
    elif cwe == "CWE-327" or "weak hashing" in title:
        changed = _simple_replace(new_lines, "hashlib.md5", "hashlib.sha256")
    elif cwe == "CWE-78" or "shell injection" in title:
        changed = _fix_shell_injection(new_lines, finding)
    elif cwe == "CWE-502" or "deserialization" in title:
        changed = _fix_pickle_loads(new_lines)
    elif cwe == "CWE-22" or "path traversal" in title:
        changed = _fix_path_traversal(new_lines, finding)
    elif cwe == "CWE-79" or "xss" in title:
        changed = _fix_dom_xss(new_lines, finding)
    elif cwe == "CWE-95" or "dynamic code" in title:
        changed = _simple_replace(new_lines, "eval(", "/* blocked eval( */")

    if not changed:
        return None

    rel_path = _relpath(file_path, root)
    diff_lines = unified_diff(
        lines,
        new_lines,
        fromfile=f"a/{rel_path}",
        tofile=f"b/{rel_path}",
        lineterm="",
    )
    diff = "\n".join(diff_lines)
    if not diff.strip():
        return None

    return PatchCandidate(diff=diff, rationale="Heuristic fix based on rule matching.")


def _relpath(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except Exception:
        return path.name


def _find_line(lines: List[str], needle: str) -> Optional[int]:
    if not needle:
        return None
    for idx, line in enumerate(lines):
        if needle.strip() and needle.strip() in line:
            return idx
    return None


def _simple_replace(lines: List[str], old: str, new: str) -> bool:
    changed = False
    for idx, line in enumerate(lines):
        if old in line:
            lines[idx] = line.replace(old, new)
            changed = True
    return changed


def _ensure_import(lines: List[str], import_stmt: str) -> None:
    if any(line.strip() == import_stmt for line in lines):
        return
    insert_at = 0
    for idx, line in enumerate(lines):
        if line.startswith("import ") or line.startswith("from "):
            insert_at = idx + 1
    lines.insert(insert_at, import_stmt)


def _fix_sql_injection(lines: List[str], finding: Finding) -> bool:
    idx = _find_line(lines, finding.evidence)
    if idx is None:
        return False
    line = lines[idx]
    indent = re.match(r"\s*", line).group(0)
    column_match = re.search(r"WHERE\s+([A-Za-z_][\w]*)\s*=", line)
    column = column_match.group(1) if column_match else "value"
    var_match = re.search(r"{([A-Za-z_][\w]*)}", line)
    var_name = var_match.group(1) if var_match else "value"
    lines[idx] = f'{indent}query = "SELECT * FROM users WHERE {column} = ?"'

    exec_idx = None
    for j in range(idx + 1, min(idx + 5, len(lines))):
        if "execute(query" in lines[j] or "cursor.execute(query" in lines[j]:
            exec_idx = j
            break
    if exec_idx is not None:
        lines[exec_idx] = re.sub(
            r"execute\(([^,\)]+)\)",
            f"execute(\\1, ({var_name},))",
            lines[exec_idx],
        )
    return True


def _fix_shell_injection(lines: List[str], finding: Finding) -> bool:
    idx = _find_line(lines, finding.evidence)
    if idx is None:
        return False
    line = lines[idx]
    if "subprocess.run" not in line:
        return False

    if "shell=True" in line:
        line = line.replace("shell=True", "shell=False")

    needs_shlex = False
    match = re.search(r"subprocess\.run\(([^,]+)", line)
    if match:
        arg = match.group(1).strip()
        if not arg.startswith("[") and "shlex.split" not in arg:
            line = line.replace(arg, f"shlex.split({arg})", 1)
            needs_shlex = True

    lines[idx] = line
    if needs_shlex:
        _ensure_import(lines, "import shlex")
    return True


def _fix_pickle_loads(lines: List[str]) -> bool:
    changed = _simple_replace(lines, "pickle.loads", "json.loads")
    if changed:
        _ensure_import(lines, "import json")
    return changed


def _fix_path_traversal(lines: List[str], finding: Finding) -> bool:
    idx = _find_line(lines, finding.evidence)
    if idx is None:
        return False
    line = lines[idx]
    indent = re.match(r"\s*", line).group(0)
    base_match = re.search(r"os\.path\.join\(([^,]+),", line)
    base_var = base_match.group(1).strip() if base_match else "base_dir"
    if "os.path.normpath" not in line:
        line = line.replace("os.path.join", "os.path.normpath(os.path.join")
        if line.count("(") > line.count(")"):
            line += ")"
    lines[idx] = line

    check_line = (
        f"{indent}if not os.path.abspath(path).startswith(os.path.abspath({base_var}) + os.sep):"
    )
    raise_line = f"{indent}    raise ValueError(\"Invalid path\")"
    insert_at = idx + 1
    lines.insert(insert_at, check_line)
    lines.insert(insert_at + 1, raise_line)
    return True


def _fix_dom_xss(lines: List[str], finding: Finding) -> bool:
    idx = _find_line(lines, finding.evidence)
    if idx is None:
        return False
    line = lines[idx]
    if ".innerHTML" in line:
        lines[idx] = line.replace(".innerHTML", ".textContent")
        return True
    if "document.write" in line:
        lines[idx] = re.sub(r"document\.write\((.+)\)", r"document.body.textContent = \1", line)
        return True
    return False
