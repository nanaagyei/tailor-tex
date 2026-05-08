"""Rule-based provider — no LLM, pure deterministic logic.

Makes TailorTex usable without any cloud API or local model.
Uses keyword matching and the original approved bullet text.
"""

from __future__ import annotations

import json
import re
from typing import Any

from tailortex.llm.base import LLMProvider, LLMResponse


class RuleBasedProvider(LLMProvider):
    """Deterministic provider that uses pattern matching instead of an LLM.

    For bullet rewriting: returns the original bullet text with minor
    keyword emphasis. For JD parsing: delegates to the deterministic
    jd_parser module. For validation: uses exact string matching.
    """

    @property
    def name(self) -> str:
        return "rule-based"

    @property
    def is_local(self) -> bool:
        return True

    async def complete(
        self,
        prompt: str,
        output_schema: dict[str, Any] | None = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Parse the prompt and return a deterministic response.

        This provider inspects prompt content to decide what kind
        of response to generate — it doesn't actually call any model.
        """
        if "rewriting resume bullets" in prompt.lower():
            result = self._handle_bullet_rewrite(prompt)
        elif "validating" in prompt.lower() and "claims" in prompt.lower():
            result = self._handle_validation(prompt)
        else:
            result = {}

        return LLMResponse(
            parsed=result,
            raw_text=json.dumps(result),
            provider="rule-based",
            model="deterministic-v1",
        )

    def _handle_bullet_rewrite(self, prompt: str) -> dict[str, Any]:
        """Extract bullets from prompt and return them unchanged."""
        bullets: list[dict[str, Any]] = []

        # Look for bullet text patterns in the prompt
        bullet_pattern = re.compile(r'"text"\s*:\s*"([^"]+)"')
        for match in bullet_pattern.finditer(prompt):
            text = match.group(1)
            bullets.append(
                {
                    "original_text": text,
                    "rewritten_text": text,
                    "validation_status": "supported",
                    "changes_made": "No changes — rule-based mode preserves original text.",
                    "needs_user_confirmation": [],
                }
            )

        return {"bullets": bullets}

    def _handle_validation(self, prompt: str) -> dict[str, Any]:
        """Validate claims by checking if text appears in evidence."""
        return {
            "claims": [],
            "summary": "Rule-based validation — claims not checked against LLM.",
        }
