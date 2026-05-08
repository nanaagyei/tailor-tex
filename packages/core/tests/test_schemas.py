"""Tests for Pydantic schema models — round-trip, validation, defaults."""

import json

import pytest
from pydantic import ValidationError

from tailortex.schemas import (
    Bullet,
    CanonicalProfile,
    ClaimResult,
    DoNotInsert,
    EvidenceLedgerEntry,
    Experience,
    GeneratedBullet,
    JDSource,
    KeywordStrategy,
    Owner,
    ParsedJobDescription,
    ResumePlan,
    RoleSignals,
    SectionPlan,
    Skill,
    SourceRef,
    TailoringOptions,
    ValidationReport,
    ValidationSummary,
    Warning,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_owner(**overrides) -> dict:
    base = {
        "full_name": "Morgan Castillo",
        "email": "morgan@example.com",
        "location": "Austin, TX",
        "links": [{"label": "GitHub", "url": "https://github.com/mcastillo"}],
    }
    base.update(overrides)
    return base


def _make_bullet(**overrides) -> dict:
    base = {
        "id": "bullet_001",
        "text": "Built CI/CD pipelines reducing deploy time by 40%.",
        "skills": ["CI/CD", "GitHub Actions"],
        "metrics": ["40% reduction"],
        "evidence_ids": ["ev_001"],
        "approved": True,
    }
    base.update(overrides)
    return base


def _make_experience(**overrides) -> dict:
    base = {
        "id": "exp_001",
        "organization": "Meridian Systems",
        "title": "Software Engineer",
        "start_date": "2023-03",
        "is_current": True,
        "approved": True,
        "bullets": [_make_bullet()],
    }
    base.update(overrides)
    return base


def _make_profile(**overrides) -> dict:
    base = {
        "profile_id": "default",
        "version": "1.0.0",
        "owner": _make_owner(),
        "summary": {"source_text": "Software engineer with 4 years experience.", "approved": True},
        "experiences": [_make_experience()],
        "projects": [],
        "education": [
            {
                "id": "edu_001",
                "institution": "UT Austin",
                "degree": "B.S.",
                "field": "Computer Science",
                "start_date": "2017-08",
                "end_date": "2021-05",
                "gpa": "3.7",
                "approved": True,
            }
        ],
        "skills": [
            {"name": "Python", "category": "Languages", "proficiency": "advanced", "approved": True}
        ],
        "evidence_ledger": [
            {
                "id": "ev_001",
                "claim_type": "experience",
                "source_text": "Built CI/CD pipelines.",
                "normalized_claim": "Maintained CI/CD pipelines.",
                "source_ref": {"document_id": "source_resume", "line_range": [14, 15]},
                "allowed_transformations": ["tighten wording"],
                "blocked_transformations": ["invent metrics"],
            }
        ],
    }
    base.update(overrides)
    return base


def _make_jd(**overrides) -> dict:
    base = {
        "job_id": "apex-backend-swe-2025",
        "source": {"type": "pasted_text"},
        "company": "Apex Engineering",
        "role_title": "Backend Software Engineer",
        "location": "Remote (US)",
        "employment_type": "Full-time",
        "seniority": "mid",
        "required_skills": ["Python", "REST APIs", "SQL"],
        "preferred_skills": ["Go", "Kubernetes"],
        "responsibilities": ["Build backend services"],
        "domain_keywords": ["backend", "microservices"],
        "role_signals": {"backend": 0.9, "frontend": 0.05},
        "prompt_injection_flags": [],
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Profile schema tests
# ---------------------------------------------------------------------------


class TestCanonicalProfile:
    def test_valid_profile_round_trip(self):
        data = _make_profile()
        profile = CanonicalProfile(**data)
        dumped = json.loads(profile.model_dump_json())
        restored = CanonicalProfile(**dumped)
        assert restored.profile_id == profile.profile_id
        assert restored.owner.full_name == "Morgan Castillo"
        assert len(restored.experiences) == 1
        assert (
            restored.experiences[0].bullets[0].text == data["experiences"][0]["bullets"][0]["text"]
        )

    def test_minimal_profile(self):
        profile = CanonicalProfile(owner=Owner(full_name="Test User"))
        assert profile.profile_id == "default"
        assert profile.version == "1.0.0"
        assert profile.experiences == []
        assert profile.skills == []
        assert profile.evidence_ledger == []

    def test_owner_requires_full_name(self):
        with pytest.raises(ValidationError):
            Owner()  # type: ignore[call-arg]

    def test_optional_fields_default_to_none(self):
        owner = Owner(full_name="Test")
        assert owner.email is None
        assert owner.phone is None
        assert owner.location is None
        assert owner.links == []

    def test_bullet_defaults(self):
        bullet = Bullet(id="b1", text="Did something.")
        assert bullet.skills == []
        assert bullet.metrics == []
        assert bullet.evidence_ids == []
        assert bullet.approved is False

    def test_experience_current_no_end_date(self):
        exp = Experience(
            id="exp_1",
            organization="Acme",
            title="Engineer",
            start_date="2024-01",
            is_current=True,
        )
        assert exp.end_date is None
        assert exp.is_current is True

    def test_skill_proficiency_validation(self):
        Skill(name="Python", proficiency="advanced")
        Skill(name="Go", proficiency="intermediate")
        Skill(name="Rust", proficiency="beginner")
        with pytest.raises(ValidationError):
            Skill(name="Bad", proficiency="expert")  # type: ignore[arg-type]

    def test_evidence_ledger_entry(self):
        entry = EvidenceLedgerEntry(
            id="ev_1",
            claim_type="experience",
            source_text="Built something.",
            normalized_claim="Built something.",
            source_ref=SourceRef(document_id="resume", line_range=(10, 12)),
        )
        assert entry.requires_user_confirmation is False
        assert entry.allowed_transformations == []
        assert entry.blocked_transformations == []

    def test_evidence_claim_type_validation(self):
        with pytest.raises(ValidationError):
            EvidenceLedgerEntry(
                id="ev_bad",
                claim_type="invalid_type",  # type: ignore[arg-type]
                source_text="x",
                normalized_claim="x",
                source_ref=SourceRef(document_id="d"),
            )


# ---------------------------------------------------------------------------
# Job description schema tests
# ---------------------------------------------------------------------------


class TestParsedJobDescription:
    def test_valid_jd_round_trip(self):
        data = _make_jd()
        jd = ParsedJobDescription(**data)
        dumped = json.loads(jd.model_dump_json())
        restored = ParsedJobDescription(**dumped)
        assert restored.job_id == jd.job_id
        assert restored.company == "Apex Engineering"
        assert restored.role_signals.backend == 0.9

    def test_minimal_jd(self):
        jd = ParsedJobDescription(
            job_id="test-jd",
            source=JDSource(type="pasted_text"),
        )
        assert jd.company is None
        assert jd.required_skills == []
        assert jd.role_signals.backend == 0.0
        assert jd.prompt_injection_flags == []

    def test_role_signals_defaults(self):
        signals = RoleSignals()
        assert signals.backend == 0.0
        assert signals.frontend == 0.0
        assert signals.machine_learning == 0.0

    def test_jd_source_types(self):
        JDSource(type="pasted_text")
        JDSource(type="url", url="https://example.com/jobs/123")
        JDSource(type="file")
        with pytest.raises(ValidationError):
            JDSource(type="unknown")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Resume plan schema tests
# ---------------------------------------------------------------------------


class TestResumePlan:
    def test_valid_plan_round_trip(self):
        plan = ResumePlan(
            resume_id="resume_001",
            target_job_id="jd_001",
            sections=[
                SectionPlan(
                    type="experience",
                    source_ids=["exp_001"],
                    selected_bullet_ids=["bullet_001"],
                    reason="Matches backend requirements.",
                )
            ],
            keyword_strategy=KeywordStrategy(
                covered=["Python", "SQL"],
                not_covered=["AWS"],
                do_not_insert=[DoNotInsert(keyword="Kubernetes", reason="No approved evidence.")],
            ),
        )
        dumped = json.loads(plan.model_dump_json())
        restored = ResumePlan(**dumped)
        assert restored.resume_id == "resume_001"
        assert len(restored.sections) == 1
        assert restored.keyword_strategy.do_not_insert[0].keyword == "Kubernetes"

    def test_generated_bullet_defaults(self):
        bullet = GeneratedBullet(id="gen_1", text="Some text.")
        assert bullet.validation_status == "needs_confirmation"
        assert bullet.validation_notes == []
        assert bullet.jd_keywords_used == []

    def test_generated_bullet_status_validation(self):
        GeneratedBullet(id="g1", text="x", validation_status="supported")
        GeneratedBullet(id="g2", text="x", validation_status="rejected")
        with pytest.raises(ValidationError):
            GeneratedBullet(id="g3", text="x", validation_status="invalid")  # type: ignore[arg-type]

    def test_tailoring_options_defaults(self):
        opts = TailoringOptions()
        assert opts.mode == "conservative"
        assert opts.max_pages == 1
        assert opts.llm_provider == "none"
        assert opts.redaction_enabled is False

    def test_tailoring_mode_validation(self):
        TailoringOptions(mode="impact_focused")
        TailoringOptions(mode="technical_depth")
        TailoringOptions(mode="research_focused")
        with pytest.raises(ValidationError):
            TailoringOptions(mode="aggressive")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Validation report schema tests
# ---------------------------------------------------------------------------


class TestValidationReport:
    def test_valid_report_round_trip(self):
        report = ValidationReport(
            resume_id="resume_001",
            status="passed_with_warnings",
            summary=ValidationSummary(
                supported_claims=5,
                needs_confirmation=1,
                rejected_claims=0,
                warnings=2,
            ),
            claims=[
                ClaimResult(
                    claim="Built CI/CD pipelines",
                    status="supported",
                    evidence_ids=["ev_001"],
                ),
                ClaimResult(
                    claim="Faster triage",
                    status="needs_confirmation",
                    evidence_ids=["ev_003"],
                ),
            ],
            warnings=[
                Warning(type="missing_keyword", message="JD mentions AWS but no evidence."),
            ],
        )
        dumped = json.loads(report.model_dump_json())
        restored = ValidationReport(**dumped)
        assert restored.resume_id == "resume_001"
        assert restored.status == "passed_with_warnings"
        assert len(restored.claims) == 2
        assert restored.summary.supported_claims == 5

    def test_report_defaults(self):
        report = ValidationReport(resume_id="r1")
        assert report.status == "passed"
        assert report.summary.supported_claims == 0
        assert report.claims == []
        assert report.warnings == []

    def test_report_status_validation(self):
        ValidationReport(resume_id="r1", status="passed")
        ValidationReport(resume_id="r2", status="failed")
        with pytest.raises(ValidationError):
            ValidationReport(resume_id="r3", status="maybe")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Cross-schema JSON serialization stability
# ---------------------------------------------------------------------------


class TestSerializationStability:
    def test_profile_json_deterministic(self):
        data = _make_profile()
        p1 = CanonicalProfile(**data)
        p2 = CanonicalProfile(**data)
        # Same input should produce identical serialization (excluding timestamps)
        d1 = p1.model_dump(exclude={"created_at", "updated_at"})
        d2 = p2.model_dump(exclude={"created_at", "updated_at"})
        assert d1 == d2

    def test_all_schemas_produce_valid_json(self):
        """Every schema should serialize to valid JSON without errors."""
        models = [
            CanonicalProfile(**_make_profile()),
            ParsedJobDescription(**_make_jd()),
            ResumePlan(resume_id="r1", target_job_id="j1"),
            GeneratedBullet(id="g1", text="text"),
            TailoringOptions(),
            ValidationReport(resume_id="r1"),
        ]
        for model in models:
            raw = model.model_dump_json()
            parsed = json.loads(raw)
            assert isinstance(parsed, dict)
