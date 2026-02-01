from __future__ import annotations

from audit.tools.openai_client import OpenAIClient


class BaseAgent:
    def __init__(self, client: OpenAIClient):
        self.client = client

    def complete(self, system: str, user: str) -> str:
        return self.client.complete(system=system, user=user)
