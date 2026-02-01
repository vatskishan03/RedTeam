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
    findings: List[HeuristicFinding] = []
    lines = text.splitlines()
    for idx, line in enumerate(lines, start=1):
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
        if "os.path.join" in line and "filename" in line:
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
    return findings
