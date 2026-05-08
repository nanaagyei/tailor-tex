"""Anthropic Claude provider."""

from __future__ import annotations

import json
from typing import Any

from tailortex.llm.base import LLMError, LLMProvider, LLMResponse


class AnthropicProvider(LLMProvider):
    """Provider for Anthropic's Claude API."""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-20250514",
        timeout: float = 60.0,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._timeout = timeout

    @property
    def name(self) -> str:
        return "anthropic"

    @property
    def is_local(self) -> bool:
        return False

    async def complete(
        self,
        prompt: str,
        output_schema: dict[str, Any] | None = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> LLMResponse | LLMError:
        try:
            import httpx
        except ImportError:
            return LLMError(
                error="httpx is required for Anthropic provider. Install with: pip install httpx",
                provider=self.name,
            )

        system_msg = "You must respond with valid JSON only. No markdown, no explanation."
        if not output_schema:
            system_msg = "You are a helpful assistant."

        body: dict[str, Any] = {
            "model": self._model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system_msg,
            "messages": [{"role": "user", "content": prompt}],
        }

        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    json=body,
                    headers=headers,
                )
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPStatusError as e:
            return LLMError(
                error=f"HTTP {e.response.status_code}: {e.response.text[:500]}",
                provider=self.name,
            )
        except httpx.RequestError as e:
            return LLMError(
                error=f"Request failed: {e}",
                provider=self.name,
            )

        raw_text = data["content"][0]["text"]
        usage = data.get("usage", {})

        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError:
            return LLMError(
                error="Response is not valid JSON",
                provider=self.name,
                raw_text=raw_text,
            )

        return LLMResponse(
            parsed=parsed,
            raw_text=raw_text,
            provider=self.name,
            model=self._model,
            usage={
                "input_tokens": usage.get("input_tokens", 0),
                "output_tokens": usage.get("output_tokens", 0),
            },
        )
