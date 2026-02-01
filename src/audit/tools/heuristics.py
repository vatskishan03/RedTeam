from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class HeuristicFinding:
    title: str
    cwe: str
    severity: str
    file: str
    line: int
    evidence: str
    impact: str
    fix_plan: str


def scan_file(path: Path, text: str) -> List[HeuristicFinding]:
    suffix = path.suffix.lower()
    if suffix in {".js", ".jsx", ".ts", ".tsx"}:
        return _scan_js(path, text)
    return _scan_python(path, text)


def _scan_python(path: Path, text: str) -> List[HeuristicFinding]:
    findings: List[HeuristicFinding] = []
    lines = text.splitlines()
    for idx, line in enumerate(lines, start=1):
        if _looks_like_path_traversal(line):
            findings.append(
                HeuristicFinding(
                    title="Path traversal risk",
                    cwe="CWE-22",
                    severity="medium",
                    file=str(path),
                    line=idx,
                    evidence=line.strip(),
                    impact="User-controlled path may escape base directory.",
                    fix_plan="Normalize and validate paths before opening.",
                )
            )
        if "pickle.loads" in line:
            findings.append(
                HeuristicFinding(
                    title="Insecure deserialization",
                    cwe="CWE-502",
                    severity="high",
                    file=str(path),
                    line=idx,
                    evidence=line.strip(),
                    impact="Untrusted pickle data can execute code.",
                    fix_plan="Avoid pickle for untrusted data; use safe serializers.",
                )
            )
        if "shell=True" in line and "subprocess" in line:
            findings.append(
                HeuristicFinding(
                    title="Shell injection",
                    cwe="CWE-78",
                    severity="high",
                    file=str(path),
                    line=idx,
                    evidence=line.strip(),
                    impact="User input can execute shell commands.",
                    fix_plan="Avoid shell=True and pass args as a list.",
                )
            )
        if "hashlib.md5" in line or "md5(" in line:
            findings.append(
                HeuristicFinding(
                    title="Weak hashing",
                    cwe="CWE-327",
                    severity="medium",
                    file=str(path),
                    line=idx,
                    evidence=line.strip(),
                    impact="MD5 is cryptographically broken.",
                    fix_plan="Use SHA-256 or a password hashing library.",
                )
            )
        if "yaml.load" in line and "SafeLoader" not in line:
            findings.append(
                HeuristicFinding(
                    title="Unsafe YAML load",
                    cwe="CWE-20",
                    severity="medium",
                    file=str(path),
                    line=idx,
                    evidence=line.strip(),
                    impact="yaml.load can construct unsafe objects.",
                    fix_plan="Use yaml.safe_load for untrusted input.",
                )
            )
        if "SELECT" in line and ("f\"" in line or "%" in line):
            findings.append(
                HeuristicFinding(
                    title="Possible SQL injection",
                    cwe="CWE-89",
                    severity="high",
                    file=str(path),
                    line=idx,
                    evidence=line.strip(),
                    impact="String-formatted SQL can be injected.",
                    fix_plan="Use parameterized queries.",
                )
            )
    return findings


def _looks_like_path_traversal(line: str) -> bool:
    lowered = line.lower()
    if "os.path.join" in line and ("filename" in lowered or "user_input" in lowered):
        return True
    if "base_dir" in lowered and "+" in line and ("user_input" in lowered or "filename" in lowered):
        return True
    if "f\"" in line or "f'" in line:
        if "{" in line and ("filename" in lowered or "user_input" in lowered or "path" in lowered):
            if "/" in line or "\\\\" in line:
                return True
    return False


def _scan_js(path: Path, text: str) -> List[HeuristicFinding]:
    findings: List[HeuristicFinding] = []
    lines = text.splitlines()
    for idx, line in enumerate(lines, start=1):
        if ".innerHTML" in line:
            findings.append(
                HeuristicFinding(
                    title="DOM XSS via innerHTML",
                    cwe="CWE-79",
                    severity="high",
                    file=str(path),
                    line=idx,
                    evidence=line.strip(),
                    impact="Untrusted input can execute script in the browser.",
                    fix_plan="Use textContent or sanitize HTML before inserting.",
                )
            )
        if "document.write" in line:
            findings.append(
                HeuristicFinding(
                    title="DOM XSS via document.write",
                    cwe="CWE-79",
                    severity="high",
                    file=str(path),
                    line=idx,
                    evidence=line.strip(),
                    impact="document.write with user input can execute script.",
                    fix_plan="Avoid document.write; use safe DOM APIs.",
                )
            )
        if "dangerouslySetInnerHTML" in line:
            findings.append(
                HeuristicFinding(
                    title="Dangerous HTML injection",
                    cwe="CWE-79",
                    severity="high",
                    file=str(path),
                    line=idx,
                    evidence=line.strip(),
                    impact="Untrusted HTML can execute script in the browser.",
                    fix_plan="Sanitize HTML or avoid dangerouslySetInnerHTML.",
                )
            )
        if "eval(" in line or "new Function" in line:
            findings.append(
                HeuristicFinding(
                    title="Dynamic code execution",
                    cwe="CWE-95",
                    severity="high",
                    file=str(path),
                    line=idx,
                    evidence=line.strip(),
                    impact="Dynamic code execution can lead to XSS or RCE.",
                    fix_plan="Avoid eval/new Function; use safer alternatives.",
                )
            )
    return findings
