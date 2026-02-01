from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional, Any
from pydantic import BaseModel, Field


class Finding(BaseModel):
    id: str
    title: str
    cwe: str
    severity: Literal["low", "medium", "high", "critical"]
    file: str
    line: int
    evidence: str
    impact: str
    fix_plan: str
    status: Literal["open", "fixed", "rejected"] = "open"


class Patch(BaseModel):
    id: str
    diff: str
    rationale: str


class VerificationResult(BaseModel):
    name: str
    command: List[str]
    exit_code: int
    stdout: str
    stderr: str
    parsed: Optional[Any] = None


class Decision(BaseModel):
    id: str
    status: Literal["fixed", "rejected"]
    reason: str


class RunBundle(BaseModel):
    run_id: str
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    target_path: str
    findings: List[Finding] = Field(default_factory=list)
    patches: List[Patch] = Field(default_factory=list)
    verification: List[VerificationResult] = Field(default_factory=list)
    decisions: List[Decision] = Field(default_factory=list)
    report_path: Optional[str] = None
    baseline_findings: Optional[List[Finding]] = None
