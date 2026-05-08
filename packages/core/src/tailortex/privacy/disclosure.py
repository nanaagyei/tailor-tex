"""Cloud LLM disclosure tracking.

Tracks which providers are cloud vs local, records user consent
decisions, and blocks cloud calls without consent.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class DisclosureRecord:
    """A single consent decision."""

    provider: str
    is_local: bool
    consented: bool
    timestamp: str
    remember: bool = False


@dataclass
class DisclosureTracker:
    """Tracks user consent for cloud LLM providers."""

    _records: list[DisclosureRecord] = field(default_factory=list)
    _remembered: dict[str, bool] = field(default_factory=dict)

    def requires_consent(self, provider_name: str, is_local: bool) -> bool:
        """Check if this provider requires user consent before use."""
        if is_local:
            return False
        return provider_name not in self._remembered

    def record_consent(
        self,
        provider_name: str,
        is_local: bool,
        consented: bool,
        remember: bool = False,
    ) -> None:
        """Record a user's consent decision."""
        record = DisclosureRecord(
            provider=provider_name,
            is_local=is_local,
            consented=consented,
            timestamp=datetime.now().isoformat(),
            remember=remember,
        )
        self._records.append(record)

        if remember and consented:
            self._remembered[provider_name] = True

    def is_allowed(self, provider_name: str, is_local: bool) -> bool:
        """Check if a provider is allowed to be used."""
        if is_local:
            return True
        if provider_name in self._remembered:
            return self._remembered[provider_name]
        return False

    def forget_provider(self, provider_name: str) -> None:
        """Remove remembered consent for a provider."""
        self._remembered.pop(provider_name, None)

    @property
    def history(self) -> list[DisclosureRecord]:
        return list(self._records)

    def build_disclosure_message(
        self,
        provider_name: str,
        data_categories: list[str],
        redaction_enabled: bool,
    ) -> str:
        """Build a human-readable disclosure message."""
        lines = [
            f"TailorTex is about to send the following data to {provider_name}:",
        ]
        for cat in data_categories:
            lines.append(f"  - {cat}")

        if redaction_enabled:
            lines.append("Contact information (name, email, phone) will be redacted.")
        else:
            lines.append("WARNING: Contact information will NOT be redacted.")

        lines.append(f"\n{provider_name}'s data handling policies are external to TailorTex.")
        lines.append("Continue? [y/N]")

        return "\n".join(lines)
