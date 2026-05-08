"""Mock LLM provider — deterministic responses for tests."""

from __future__ import annotations

import json
from typing import Any

from tailortex.llm.base import LLMError, LLMProvider, LLMResponse


class MockProvider(LLMProvider):
    """Returns canned responses for testing.

    Supply a list of responses; each call pops the next one.
    If no responses remain, returns a generic empty JSON object.
    """

    def __init__(self, responses: list[dict[str, Any]] | None = None) -> None:
        self._responses: list[dict[str, Any]] = list(responses or [])
        self.call_log: list[str] = []

    @property
    def name(self) -> str:
        return "mock"

    @property
    def is_local(self) -> bool:
        return True

    async def complete(
        self,
        prompt: str,
        output_schema: dict[str, Any] | None = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> LLMResponse | LLMError:
        self.call_log.append(prompt)

        if self._responses:
            data = self._responses.pop(0)
        else:
            data = {}

        raw = json.dumps(data)
        return LLMResponse(
            parsed=data,
            raw_text=raw,
            provider="mock",
            model="mock-v1",
        )

    def add_response(self, response: dict[str, Any]) -> None:
        """Queue a response for the next call."""
        self._responses.append(response)

    def add_error(self, error_msg: str) -> None:
        """Queue an error response (stored as special dict)."""
        self._responses.append({"__mock_error__": error_msg})

    async def complete(
        self,
        prompt: str,
        output_schema: dict[str, Any] | None = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> LLMResponse | LLMError:
        self.call_log.append(prompt)

        if self._responses:
            data = self._responses.pop(0)
        else:
            data = {}

        if isinstance(data, dict) and "__mock_error__" in data:
            return LLMError(
                error=data["__mock_error__"],
                provider="mock",
            )

        raw = json.dumps(data)
        return LLMResponse(
            parsed=data,
            raw_text=raw,
            provider="mock",
            model="mock-v1",
        )
