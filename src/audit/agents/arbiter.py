from __future__ import annotations

from typing import List

from audit.agents.base import BaseAgent
from audit.agents.prompts import ARBITER_SYSTEM
from audit.contracts import Decision, Finding, Patch, VerificationResult
from audit.tools.jsonio import extract_json


class ArbiterAgent(BaseAgent):
    def run(
        self,
        findings: List[Finding],
        patches: List[Patch],
        verification: List[VerificationResult],
    ) -> List[Decision]:
        findings_json = [f.model_dump() for f in findings]
        patches_json = [p.model_dump() for p in patches]
        verification_json = [v.model_dump() for v in verification]
        user_prompt = (
            "Decide if each finding is fixed based on patches and tool outputs.\n"
            "Reject if evidence suggests the issue remains.\n\n"
            f"Findings:\n{findings_json}\n\n"
            f"Patches:\n{patches_json}\n\n"
            f"Verification:\n{verification_json}\n"
        )
        raw = self.complete(ARBITER_SYSTEM, user_prompt)
        payload = extract_json(raw)
        decisions_payload = payload.get("decisions", []) if isinstance(payload, dict) else payload
        decisions: List[Decision] = []
        for item in decisions_payload:
            decisions.append(Decision.model_validate(item))
        return decisions
