"""Tests for redaction and disclosure tracking."""

from tailortex.privacy.disclosure import DisclosureTracker
from tailortex.privacy.redaction import RedactionMap, build_redaction_map, redact_profile_text


class TestRedactionMap:
    def test_add_and_redact(self):
        rmap = RedactionMap()
        rmap.add("Prince Agyei", "CANDIDATE_NAME")
        result = rmap.redact("My name is Prince Agyei and I work hard.")
        assert "Prince Agyei" not in result
        assert "CANDIDATE_NAME" in result

    def test_rehydrate(self):
        rmap = RedactionMap()
        rmap.add("Prince Agyei", "CANDIDATE_NAME")
        redacted = rmap.redact("Hello Prince Agyei!")
        restored = rmap.rehydrate(redacted)
        assert restored == "Hello Prince Agyei!"

    def test_round_trip(self):
        rmap = RedactionMap()
        rmap.add("Jane Doe", "CANDIDATE_NAME")
        rmap.add("jane@example.com", "REDACTED_EMAIL")
        rmap.add("Acme Corp", "COMPANY")
        rmap.add("Widget Inc", "COMPANY")

        original = "Jane Doe works at Acme Corp and Widget Inc. Email: jane@example.com"
        redacted = rmap.redact(original)

        assert "Jane Doe" not in redacted
        assert "jane@example.com" not in redacted
        assert "Acme Corp" not in redacted
        assert "Widget Inc" not in redacted

        assert "CANDIDATE_NAME" in redacted
        assert "REDACTED_EMAIL" in redacted
        assert "COMPANY" in redacted
        assert "COMPANY_2" in redacted

        restored = rmap.rehydrate(redacted)
        assert restored == original

    def test_empty_string_passthrough(self):
        rmap = RedactionMap()
        assert rmap.add("", "CANDIDATE_NAME") == ""
        assert rmap.add("   ", "CANDIDATE_NAME") == "   "

    def test_duplicate_add_returns_same_placeholder(self):
        rmap = RedactionMap()
        p1 = rmap.add("Acme", "COMPANY")
        p2 = rmap.add("Acme", "COMPANY")
        assert p1 == p2

    def test_multiple_companies_numbered(self):
        rmap = RedactionMap()
        p1 = rmap.add("Acme Corp", "COMPANY")
        p2 = rmap.add("Widget Inc", "COMPANY")
        assert p1 == "COMPANY"
        assert p2 == "COMPANY_2"

    def test_mappings_property(self):
        rmap = RedactionMap()
        rmap.add("Jane", "CANDIDATE_NAME")
        assert rmap.mappings == {"Jane": "CANDIDATE_NAME"}


class TestBuildRedactionMap:
    def test_builds_complete_map(self):
        rmap = build_redaction_map(
            full_name="Jane Doe",
            email="jane@test.com",
            phone="555-1234",
            location="Austin, TX",
            companies=["Acme", "Widget"],
            institutions=["MIT"],
        )
        text = "Jane Doe at Acme and Widget, MIT grad. jane@test.com 555-1234 Austin, TX"
        redacted = rmap.redact(text)

        assert "Jane Doe" not in redacted
        assert "jane@test.com" not in redacted
        assert "555-1234" not in redacted
        assert "Austin, TX" not in redacted
        assert "Acme" not in redacted
        assert "Widget" not in redacted
        assert "MIT" not in redacted

    def test_none_fields_skipped(self):
        rmap = build_redaction_map(full_name="Jane")
        assert len(rmap.mappings) == 1


class TestRedactProfileText:
    def test_returns_tuple(self):
        text = "Jane Doe works at Acme"
        redacted, rmap = redact_profile_text(text, full_name="Jane Doe", companies=["Acme"])
        assert "Jane Doe" not in redacted
        assert "Acme" not in redacted
        assert isinstance(rmap, RedactionMap)

    def test_rehydrate_from_returned_map(self):
        text = "Jane Doe at Acme"
        redacted, rmap = redact_profile_text(text, full_name="Jane Doe", companies=["Acme"])
        restored = rmap.rehydrate(redacted)
        assert restored == text


class TestDisclosureTracker:
    def test_local_provider_no_consent_needed(self):
        tracker = DisclosureTracker()
        assert tracker.requires_consent("ollama", is_local=True) is False

    def test_cloud_provider_requires_consent(self):
        tracker = DisclosureTracker()
        assert tracker.requires_consent("anthropic", is_local=False) is True

    def test_remembered_consent(self):
        tracker = DisclosureTracker()
        tracker.record_consent("anthropic", is_local=False, consented=True, remember=True)
        assert tracker.requires_consent("anthropic", is_local=False) is False
        assert tracker.is_allowed("anthropic", is_local=False) is True

    def test_non_remembered_consent_still_requires(self):
        tracker = DisclosureTracker()
        tracker.record_consent("anthropic", is_local=False, consented=True, remember=False)
        assert tracker.requires_consent("anthropic", is_local=False) is True

    def test_local_always_allowed(self):
        tracker = DisclosureTracker()
        assert tracker.is_allowed("ollama", is_local=True) is True

    def test_cloud_not_allowed_without_consent(self):
        tracker = DisclosureTracker()
        assert tracker.is_allowed("anthropic", is_local=False) is False

    def test_forget_provider(self):
        tracker = DisclosureTracker()
        tracker.record_consent("anthropic", is_local=False, consented=True, remember=True)
        tracker.forget_provider("anthropic")
        assert tracker.requires_consent("anthropic", is_local=False) is True

    def test_history(self):
        tracker = DisclosureTracker()
        tracker.record_consent("anthropic", is_local=False, consented=True)
        tracker.record_consent("openai", is_local=False, consented=False)
        assert len(tracker.history) == 2
        assert tracker.history[0].provider == "anthropic"
        assert tracker.history[1].consented is False

    def test_disclosure_message(self):
        tracker = DisclosureTracker()
        msg = tracker.build_disclosure_message(
            provider_name="Anthropic",
            data_categories=["8 approved bullets", "target job description"],
            redaction_enabled=True,
        )
        assert "Anthropic" in msg
        assert "8 approved bullets" in msg
        assert "redacted" in msg.lower()

    def test_disclosure_message_no_redaction(self):
        tracker = DisclosureTracker()
        msg = tracker.build_disclosure_message(
            provider_name="OpenAI",
            data_categories=["profile data"],
            redaction_enabled=False,
        )
        assert "WARNING" in msg
        assert "NOT" in msg
