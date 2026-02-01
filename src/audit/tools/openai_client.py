from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any

from audit.config import settings


@dataclass
class OpenAIClient:
    model: str = settings.model
    temperature: float = settings.temperature
    max_tokens: int = settings.max_tokens

    def __post_init__(self) -> None:
        self._client = None
        self.available = False
        self.error = None
        try:
            from openai import OpenAI
            import httpx

            timeout_s = float(os.getenv("AUDIT_OPENAI_TIMEOUT_S", "30"))
            max_retries = int(os.getenv("AUDIT_OPENAI_MAX_RETRIES", "0"))
            http_client = httpx.Client(timeout=httpx.Timeout(timeout_s))
            self._client = OpenAI(
                timeout=timeout_s,
                max_retries=max_retries,
                http_client=http_client,
            )
            self.available = True
        except Exception as exc:
            self.error = str(exc)

    def complete(self, system: str, user: str) -> str:
        if not self.available or self._client is None:
            raise RuntimeError(f"OpenAI client unavailable: {self.error}")

        if hasattr(self._client, "responses"):
            try:
                response = self._client.responses.create(
                    model=self.model,
                    input=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens,
                )
            except TypeError:
                response = self._client.responses.create(
                    model=self.model,
                    input=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )
        else:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
        return _extract_text(response)


def _extract_text(response: Any) -> str:
    if response is None:
        return ""
    if hasattr(response, "output_text"):
        return response.output_text
    if hasattr(response, "choices"):
        choice = response.choices[0]
        if hasattr(choice, "message"):
            return choice.message.content or ""
        if hasattr(choice, "text"):
            return choice.text or ""
    if hasattr(response, "output"):
        try:
            for item in response.output:
                if hasattr(item, "content"):
                    content = item.content
                    if content and hasattr(content[0], "text"):
                        return content[0].text
        except Exception:
            pass
    if isinstance(response, dict):
        if "output_text" in response:
            return response["output_text"]
        if "choices" in response and response["choices"]:
            choice = response["choices"][0]
            if "message" in choice and "content" in choice["message"]:
                return choice["message"]["content"]
            if "text" in choice:
                return choice["text"]
    return ""
