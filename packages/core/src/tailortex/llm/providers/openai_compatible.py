"""OpenAI-compatible provider.

Works with OpenAI, LM Studio, and any API that implements the
OpenAI chat completions format.
"""

from __future__ import annotations

import json
from typing import Any

from tailortex.llm.base import LLMError, LLMProvider, LLMResponse


class OpenAICompatibleProvider(LLMProvider):
    """Provider for OpenAI-compatible APIs (OpenAI, LM Studio, etc.)."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        base_url: str = "https://api.openai.com/v1",
        timeout: float = 60.0,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    @property
    def name(self) -> str:
        return "openai-compatible"

    @property
    def is_local(self) -> bool:
        return "localhost" in self._base_url or "127.0.0.1" in self._base_url

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
                error="httpx is required for OpenAI-compatible provider. Install with: pip install httpx",
                provider=self.name,
            )

        messages = [{"role": "user", "content": prompt}]
        if output_schema:
            messages.insert(0, {
                "role": "system",
                "content": "You must respond with valid JSON only. No markdown, no explanation.",
            })

        body: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if output_schema:
            body["response_format"] = {"type": "json_object"}

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(
                    f"{self._base_url}/chat/completions",
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

        raw_text = data["choices"][0]["message"]["content"]
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
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
            },
        )
