"""Abstract LLM provider interface.

All providers implement `complete()` — takes a prompt + output schema,
returns a parsed response or structured error.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LLMResponse:
    """Structured response from an LLM provider."""

    parsed: dict[str, Any] | list[Any]
    raw_text: str
    provider: str
    model: str
    usage: dict[str, int] = field(default_factory=dict)


@dataclass
class LLMError:
    """Structured error when LLM call fails."""

    error: str
    provider: str
    retries_attempted: int = 0
    raw_text: str | None = None


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider name."""

    @property
    @abstractmethod
    def is_local(self) -> bool:
        """True if the provider runs locally (no cloud calls)."""

    @abstractmethod
    async def complete(
        self,
        prompt: str,
        output_schema: dict[str, Any] | None = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> LLMResponse | LLMError:
        """Send a prompt to the LLM and return a parsed response.

        If output_schema is provided, the response must be valid JSON
        matching that schema. On malformed JSON, retry once with a
        repair prompt. If repair fails, return LLMError.
        """

    async def complete_with_retry(
        self,
        prompt: str,
        output_schema: dict[str, Any] | None = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> LLMResponse | LLMError:
        """Complete with one automatic retry on JSON parse failure."""
        result = await self.complete(prompt, output_schema, temperature, max_tokens)

        if isinstance(result, LLMError) and result.raw_text and output_schema:
            repair_prompt = (
                "The previous response was not valid JSON. "
                "Please fix the JSON and return only valid JSON matching the schema.\n\n"
                f"Original response:\n{result.raw_text}\n\n"
                f"Required schema:\n{json.dumps(output_schema, indent=2)}"
            )
            repair_result = await self.complete(
                repair_prompt, output_schema, temperature, max_tokens
            )
            if isinstance(repair_result, LLMResponse):
                return repair_result
            return LLMError(
                error=f"Retry failed: {repair_result.error}",
                provider=self.name,
                retries_attempted=1,
                raw_text=repair_result.raw_text,
            )

        return result
