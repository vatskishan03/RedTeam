from __future__ import annotations

from typing import List

from audit.agents.base import BaseAgent
from audit.agents.prompts import RED_SYSTEM, VULN_CATEGORIES
from audit.contracts import Finding
from audit.tools.jsonio import extract_json


class RedTeamAgent(BaseAgent):
    def run(self, code_context: str, max_findings: int = 12) -> List[Finding]:
        user_prompt = (
            "Scan the code context for vulnerabilities. Focus on these categories:\n"
            + "- "
            + "\n- ".join(VULN_CATEGORIES)
            + "\n\n"
            + f"Limit to at most {max_findings} findings.\n\n"
            + "Return JSON only.\n\n"
            + code_context
        )
        raw = self.complete(RED_SYSTEM, user_prompt)
        payload = extract_json(raw)
        findings_payload = payload.get("findings", []) if isinstance(payload, dict) else payload
        findings: List[Finding] = []
        for item in findings_payload:
            findings.append(Finding.model_validate(item))
        return findings

    @staticmethod
    def from_heuristics(findings: List[dict]) -> List[Finding]:
        return [Finding.model_validate(item) for item in findings]
