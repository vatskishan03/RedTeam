from __future__ import annotations

from typing import List

from audit.agents.base import BaseAgent
from audit.agents.prompts import BLUE_SYSTEM
from audit.contracts import Finding, Patch
from audit.tools.jsonio import extract_json


class BlueTeamAgent(BaseAgent):
    def run(self, code_context: str, findings: List[Finding]) -> List[Patch]:
        findings_json = [f.model_dump() for f in findings]
        user_prompt = (
            "Propose minimal patches for the findings below.\n"
            "Return only unified diffs.\n\n"
            f"Findings JSON:\n{findings_json}\n\n"
            "Code context:\n"
            + code_context
        )
        raw = self.complete(BLUE_SYSTEM, user_prompt)
        payload = extract_json(raw)
        patches_payload = payload.get("patches", []) if isinstance(payload, dict) else payload
        patches: List[Patch] = []
        for item in patches_payload:
            patches.append(Patch.model_validate(item))
        return patches
