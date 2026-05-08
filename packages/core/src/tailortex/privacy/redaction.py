"""PII redaction and rehydration for cloud LLM calls.

Replaces sensitive entities before sending data to a cloud provider,
then restores them locally after receiving the response.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class RedactionMap:
    """Bidirectional mapping between original values and placeholders."""

    _forward: dict[str, str] = field(default_factory=dict)
    _reverse: dict[str, str] = field(default_factory=dict)
    _counters: dict[str, int] = field(default_factory=dict)

    def add(self, original: str, category: str) -> str:
        """Register a value for redaction and return its placeholder."""
        if not original or not original.strip():
            return original

        key = original.strip()
        if key in self._forward:
            return self._forward[key]

        count = self._counters.get(category, 0) + 1
        self._counters[category] = count

        if count == 1:
            placeholder = category
        else:
            placeholder = f"{category}_{count}"

        self._forward[key] = placeholder
        self._reverse[placeholder] = key
        return placeholder

    def redact(self, text: str) -> str:
        """Replace all known originals with their placeholders."""
        result = text
        # Sort by length descending to avoid partial replacements
        for original in sorted(self._forward, key=len, reverse=True):
            placeholder = self._forward[original]
            result = result.replace(original, placeholder)
        return result

    def rehydrate(self, text: str) -> str:
        """Replace all placeholders with their original values."""
        result = text
        # Sort by length descending to avoid partial replacements
        for placeholder in sorted(self._reverse, key=len, reverse=True):
            original = self._reverse[placeholder]
            result = result.replace(placeholder, original)
        return result

    @property
    def mappings(self) -> dict[str, str]:
        """Return the forward mapping (original → placeholder)."""
        return dict(self._forward)


def build_redaction_map(
    full_name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    location: str | None = None,
    companies: list[str] | None = None,
    institutions: list[str] | None = None,
    urls: list[str] | None = None,
) -> RedactionMap:
    """Build a redaction map from profile data."""
    rmap = RedactionMap()

    if full_name:
        rmap.add(full_name, "CANDIDATE_NAME")

    if email:
        rmap.add(email, "REDACTED_EMAIL")

    if phone:
        rmap.add(phone, "REDACTED_PHONE")

    if location:
        rmap.add(location, "REDACTED_LOCATION")

    for company in (companies or []):
        rmap.add(company, "COMPANY")

    for inst in (institutions or []):
        rmap.add(inst, "UNIVERSITY")

    for url in (urls or []):
        rmap.add(url, "REDACTED_URL")

    return rmap


def redact_profile_text(
    text: str,
    full_name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    location: str | None = None,
    companies: list[str] | None = None,
    institutions: list[str] | None = None,
) -> tuple[str, RedactionMap]:
    """Convenience: build a redaction map and apply it to text."""
    rmap = build_redaction_map(
        full_name=full_name,
        email=email,
        phone=phone,
        location=location,
        companies=companies,
        institutions=institutions,
    )
    return rmap.redact(text), rmap
