"""TailorTex privacy and redaction system."""

from tailortex.privacy.disclosure import DisclosureRecord, DisclosureTracker
from tailortex.privacy.redaction import RedactionMap, build_redaction_map, redact_profile_text

__all__ = [
    "DisclosureRecord",
    "DisclosureTracker",
    "RedactionMap",
    "build_redaction_map",
    "redact_profile_text",
]
