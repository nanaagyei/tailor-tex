"""Ollama provider — local LLM inference."""

from __future__ import annotations

import json
from typing import Any

from tailortex.llm.base import LLMError, LLMProvider, LLMResponse


class OllamaProvider(LLMProvider):
    """Provider for Ollama local inference server."""

    def __init__(
        self,
        model: str = "llama3.1",
        base_url: str = "http://localhost:11434",
        timeout: float = 120.0,
    ) -> None:
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    @property
    def name(self) -> str:
        return "ollama"

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
        try:
            import httpx
        except ImportError:
            return LLMError(
                error="httpx is required for Ollama provider. Install with: pip install httpx",
                provider=self.name,
            )

        if output_schema:
            prompt = (
                "You must respond with valid JSON only. No markdown, no explanation.\n\n"
                + prompt
            )

        body: dict[str, Any] = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        if output_schema:
            body["format"] = "json"

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(
                    f"{self._base_url}/api/generate",
                    json=body,
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
                error=f"Ollama connection failed: {e}. Is Ollama running?",
                provider=self.name,
            )

        raw_text = data.get("response", "")

        if output_schema:
            try:
                parsed = json.loads(raw_text)
            except json.JSONDecodeError:
                return LLMError(
                    error="Response is not valid JSON",
                    provider=self.name,
                    raw_text=raw_text,
                )
        else:
            parsed = {"text": raw_text}

        return LLMResponse(
            parsed=parsed,
            raw_text=raw_text,
            provider=self.name,
            model=self._model,
        )
