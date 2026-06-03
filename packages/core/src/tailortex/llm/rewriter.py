"""Bullet rewriter — generates tailored resume bullets.

4 modes: conservative, impact-focused, technical-depth, research-focused.
Uses evidence-constrained prompts. Falls back to original text
when no LLM is available.

Automatically applies PII redaction before sending prompts to cloud providers
and rehydrates responses after receiving them.
"""

from __future__ import annotations

import json
import uuid
from typing import Any

from tailortex.llm.base import LLMError, LLMProvider, LLMResponse
from tailortex.llm.prompts import BULLET_REWRITE_PROMPT, MODE_INSTRUCTIONS
from tailortex.privacy.redaction import RedactionMap
from tailortex.schemas.profile import Bullet
from tailortex.schemas.resume import GeneratedBullet


def _uid() -> str:
    return uuid.uuid4().hex[:12]


async def rewrite_bullets(
    bullets: list[Bullet],
    jd_skills: list[str],
    jd_responsibilities: list[str],
    provider: LLMProvider,
    mode: str = "conservative",
    redaction_map: RedactionMap | None = None,
) -> list[GeneratedBullet]:
    """Rewrite bullets using the LLM provider.

    Falls back to original text if the provider fails.
    If a redaction_map is provided and the provider is not local,
    PII in the prompt is redacted before sending and rehydrated in the response.
    """
    evidence = json.dumps(
        [
            {
                "id": b.id,
                "text": b.text,
                "skills": b.skills,
                "metrics": b.metrics,
                "approved": b.approved,
            }
            for b in bullets
        ],
        indent=2,
    )

    parsed_job = json.dumps(
        {
            "skills": jd_skills,
            "responsibilities": jd_responsibilities,
        },
        indent=2,
    )

    generated_bullet_schema = json.dumps(
        {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "source_bullet_id": {"type": "string"},
                    "text": {"type": "string"},
                    "jd_keywords_used": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "validation_notes": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": [
                    "source_bullet_id",
                    "text",
                    "jd_keywords_used",
                    "validation_notes",
                ],
            },
        },
        indent=2,
    )

    prompt = BULLET_REWRITE_PROMPT.format(
        mode=mode,
        approved_evidence=evidence,
        parsed_job=parsed_job,
        generated_bullet_schema=generated_bullet_schema,
    )

    should_redact = redaction_map is not None and not provider.is_local

    if should_redact:
        prompt = redaction_map.redact(prompt)

    result = await provider.complete_with_retry(
        prompt,
        output_schema={"type": "array"},
    )

    if isinstance(result, LLMError):
        return _fallback_bullets(bullets)

    if should_redact:
        result = LLMResponse(
            parsed=result.parsed,
            raw_text=redaction_map.rehydrate(result.raw_text),
            provider=result.provider,
            model=result.model,
            usage=result.usage,
        )

    return _parse_rewrite_response(result.parsed, bullets)


def _fallback_bullets(bullets: list[Bullet]) -> list[GeneratedBullet]:
    """Return original bullets unchanged when LLM is unavailable."""
    return [
        GeneratedBullet(
            id=f"gen-{b.id}",
            text=b.text,
            source_bullet_ids=[b.id],
            validation_status="supported",
            validation_notes=["No changes — using original text."],
        )
        for b in bullets
    ]


def _parse_rewrite_response(
    parsed: Any,
    original_bullets: list[Bullet],
) -> list[GeneratedBullet]:
    """Parse LLM response into GeneratedBullet objects."""
    results: list[GeneratedBullet] = []

    items = parsed if isinstance(parsed, list) else parsed.get("bullets", [])
    {b.id: b for b in original_bullets}

    for item in items:
        source_id = item.get("source_bullet_id", "")

        results.append(
            GeneratedBullet(
                id=f"gen-{_uid()}",
                text=item.get("text", ""),
                source_bullet_ids=[source_id] if source_id else [],
                jd_keywords_used=item.get("jd_keywords_used", []),
                validation_status="needs_confirmation",
                validation_notes=item.get("validation_notes", []),
            )
        )

    # Add any bullets that the LLM missed
    seen_source_ids = set()
    for r in results:
        seen_source_ids.update(r.source_bullet_ids)

    for b in original_bullets:
        if b.id not in seen_source_ids:
            results.append(
                GeneratedBullet(
                    id=f"gen-{b.id}",
                    text=b.text,
                    source_bullet_ids=[b.id],
                    validation_status="supported",
                    validation_notes=["Not processed by LLM — original text preserved."],
                )
            )

    return results


def rewrite_bullets_deterministic(
    bullets: list[Bullet],
    jd_skills: list[str],
) -> list[GeneratedBullet]:
    """Deterministic rewrite — no LLM. Returns originals unchanged."""
    return _fallback_bullets(bullets)
