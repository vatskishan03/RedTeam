from __future__ import annotations

from typing import List

from audit.agents.base import BaseAgent
from audit.agents.prompts import REPORTER_SYSTEM
from audit.contracts import Decision, Finding, Patch, VerificationResult


class ReporterAgent(BaseAgent):
    def run(
        self,
        target_path: str,
        findings: List[Finding],
        patches: List[Patch],
        verification: List[VerificationResult],
        decisions: List[Decision],
        baseline: List[Finding] | None = None,
        reattack: List[Finding] | None = None,
    ) -> str:
        payload = {
            "target_path": target_path,
            "findings": [f.model_dump() for f in findings],
            "patches": [p.model_dump() for p in patches],
            "verification": [v.model_dump() for v in verification],
            "decisions": [d.model_dump() for d in decisions],
            "baseline": [f.model_dump() for f in baseline] if baseline else None,
            "reattack": [f.model_dump() for f in reattack] if reattack else None,
        }
        user_prompt = (
            "Write a concise Markdown security report.\n"
            "Include: summary, findings table, patches, verification results, next steps.\n"
            "If baseline is provided, include a small scorecard.\n\n"
            f"Payload:\n{payload}\n"
        )
        return self.complete(REPORTER_SYSTEM, user_prompt)
