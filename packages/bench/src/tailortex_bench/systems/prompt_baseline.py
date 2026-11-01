"""Versioned prompt-only baseline."""

from __future__ import annotations

import asyncio
import os
from typing import Any

from tailortex.llm.base import LLMError, LLMProvider
from tailortex.llm.providers.anthropic import AnthropicProvider
from tailortex.llm.providers.mock import MockProvider
from tailortex.llm.providers.ollama import OllamaProvider
from tailortex.llm.providers.openai_compatible import OpenAICompatibleProvider

from tailortex_bench.corpus import ROOT, Case


class ProviderError(ValueError):
    """Provider configuration or request failed."""


class PromptBaseline:
    id = "prompt-baseline"
    kind = "prompt-baseline"

    def __init__(self, provider: str, model: str | None) -> None:
        if provider != "mock" and not model:
            raise ProviderError("Missing --model for non-mock provider")
        if provider in ("anthropic", "openai"):
            key_name = f"TAILORTEX_{provider.upper()}_API_KEY"
            if not os.getenv(key_name):
                raise ProviderError(f"Missing {key_name}; no request made")
        if provider not in ("mock", "anthropic", "openai", "ollama"):
            raise ProviderError(f"Unknown provider: {provider}")
        self.provider = provider
        self.model = model or "mock-v1"
        self._notified = False

    def run(self, case: Case) -> dict[str, Any]:
        template = (ROOT / "benchmark/prompts/baseline-v1.md").read_text(encoding="utf-8")
        evidence = "\n".join(
            f"- {item['text']} ({item['owner']})" for item in case.dossier["evidence"]
        )
        prompt = (
            template.replace("{{BASE_RESUME}}", case.resume)
            .replace("{{EVIDENCE}}", evidence)
            .replace("{{JOB_DESCRIPTION}}", case.job)
        )
        llm: LLMProvider
        if self.provider == "mock":
            llm = MockProvider([{"resume": case.resume}])
        elif self.provider == "anthropic":
            llm = AnthropicProvider(os.environ["TAILORTEX_ANTHROPIC_API_KEY"], self.model)
        elif self.provider == "openai":
            llm = OpenAICompatibleProvider(os.environ["TAILORTEX_OPENAI_API_KEY"], self.model)
        else:
            llm = OllamaProvider(model=self.model)
        if self.provider in ("anthropic", "openai") and not self._notified:
            print("Synthetic corpus text will be sent to the selected cloud provider.")
            self._notified = True
        response = asyncio.run(llm.complete(prompt, temperature=0))
        if isinstance(response, LLMError):
            raise ProviderError(response.error)
        output = (
            (response.parsed.get("resume") if isinstance(response.parsed, dict) else None)
            if self.provider == "mock"
            else response.raw_text
        )
        if not isinstance(output, str):
            raise ProviderError("Provider returned no resume text")
        return {
            "text": output,
            "version": "baseline-v1",
            "model": {
                "provider": self.provider,
                "name": self.model,
                "version": response.model,
                "temperature": 0,
            },
        }
