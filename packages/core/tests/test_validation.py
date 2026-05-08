"""Golden tests for claim validation — fabrication must be rejected."""

from tailortex.llm.providers.mock import MockProvider
from tailortex.llm.rewriter import rewrite_bullets, rewrite_bullets_deterministic
from tailortex.schemas.profile import (
    Bullet,
    CanonicalProfile,
    Education,
    Experience,
    Owner,
    Project,
    Skill,
)
from tailortex.schemas.resume import GeneratedBullet
from tailortex.validation.claim_validator import validate_claims


def _make_profile() -> CanonicalProfile:
    """Profile with Python/Docker experience but NO Kubernetes, NO leadership."""
    return CanonicalProfile(
        owner=Owner(full_name="Test User", email="test@example.com"),
        experiences=[
            Experience(
                id="exp-1",
                organization="Acme Corp",
                title="Software Engineer",
                start_date="2023-01",
                is_current=True,
                approved=True,
                bullets=[
                    Bullet(
                        id="b-1",
                        text=(
                            "Built REST API endpoints using Python and FastAPI "
                            "serving 5k requests/sec"
                        ),
                        skills=["Python", "FastAPI", "REST"],
                        approved=True,
                        metrics=["5k requests/sec"],
                    ),
                    Bullet(
                        id="b-2",
                        text="Deployed containerized services using Docker and CI/CD pipelines",
                        skills=["Docker", "CI/CD"],
                        approved=True,
                        metrics=[],
                    ),
                ],
            ),
        ],
        projects=[
            Project(
                id="proj-1",
                name="LogPipe",
                description="Log aggregation tool",
                skills=["Python", "PostgreSQL"],
                bullets=[
                    Bullet(
                        id="b-3",
                        text="Built a log aggregation pipeline processing 100k events/day",
                        skills=["Python", "PostgreSQL"],
                        approved=True,
                        metrics=["100k events/day"],
                    ),
                ],
            ),
        ],
        skills=[
            Skill(name="Python"),
            Skill(name="FastAPI"),
            Skill(name="Docker"),
            Skill(name="PostgreSQL"),
            Skill(name="CI/CD"),
            Skill(name="REST"),
        ],
        education=[
            Education(
                id="edu-1",
                institution="UT Austin",
                degree="B.S.",
                field="Computer Science",
                start_date="2017-08",
                end_date="2021-05",
            ),
        ],
    )


class TestGoldenFabricationRejection:
    """Golden tests from the spec — these must always pass."""

    def test_kubernetes_fabrication_rejected(self):
        """JD asks for Kubernetes, profile does not include Kubernetes."""
        profile = _make_profile()
        bullet = GeneratedBullet(
            id="gen-b-2",
            text=(
                "Orchestrated containerized microservices using Docker and Kubernetes in production"
            ),
            source_bullet_ids=["b-2"],
            validation_status="needs_confirmation",
        )
        report = validate_claims([bullet], profile)
        k8s_claim = report.claims[0]
        assert k8s_claim.status == "rejected"
        assert (
            "kubernetes" in k8s_claim.claim.lower() or "not in evidence" in k8s_claim.claim.lower()
        )

    def test_leadership_fabrication_rejected(self):
        """JD asks for 'led a team', profile has no leadership evidence."""
        profile = _make_profile()
        bullet = GeneratedBullet(
            id="gen-b-1",
            text="Led a team of 5 engineers building REST API endpoints using Python and FastAPI",
            source_bullet_ids=["b-1"],
            validation_status="needs_confirmation",
        )
        report = validate_claims([bullet], profile)
        claim = report.claims[0]
        assert claim.status == "rejected"
        assert "leadership" in claim.claim.lower() or "scope" in claim.claim.lower()

    def test_metric_fabrication_rejected(self):
        """JD asks for 'reduced latency by 40%', profile has no such metric."""
        profile = _make_profile()
        bullet = GeneratedBullet(
            id="gen-b-1",
            text="Built REST API endpoints using Python and FastAPI, reducing latency by 40%",
            source_bullet_ids=["b-1"],
            validation_status="needs_confirmation",
        )
        report = validate_claims([bullet], profile)
        claim = report.claims[0]
        assert claim.status == "rejected"
        assert "40%" in claim.claim or "fabricated" in claim.claim.lower()

    def test_unchanged_text_supported(self):
        """Original text preserved should be marked supported."""
        profile = _make_profile()
        bullet = GeneratedBullet(
            id="gen-b-1",
            text="Built REST API endpoints using Python and FastAPI serving 5k requests/sec",
            source_bullet_ids=["b-1"],
            validation_status="needs_confirmation",
        )
        report = validate_claims([bullet], profile)
        assert report.claims[0].status == "supported"

    def test_existing_metric_preserved_is_supported(self):
        """Rewritten text keeping existing metric should pass."""
        profile = _make_profile()
        bullet = GeneratedBullet(
            id="gen-b-1",
            text=(
                "Developed high-performance REST API endpoints with Python "
                "and FastAPI handling 5k requests/sec"
            ),
            source_bullet_ids=["b-1"],
            validation_status="needs_confirmation",
        )
        report = validate_claims([bullet], profile)
        claim = report.claims[0]
        assert claim.status != "rejected"

    def test_report_fails_on_any_rejection(self):
        """Report status must be 'failed' if any claim is rejected."""
        profile = _make_profile()
        bullets = [
            GeneratedBullet(
                id="gen-b-1",
                text="Built REST API endpoints",
                source_bullet_ids=["b-1"],
                validation_status="supported",
            ),
            GeneratedBullet(
                id="gen-b-2",
                text="Deployed microservices using Docker and Kubernetes on AWS EKS",
                source_bullet_ids=["b-2"],
                validation_status="needs_confirmation",
            ),
        ]
        report = validate_claims(bullets, profile)
        assert report.status == "failed"
        assert report.summary.rejected_claims > 0

    def test_report_passes_when_all_supported(self):
        """Report passes when all claims are supported."""
        profile = _make_profile()
        bullets = [
            GeneratedBullet(
                id="gen-b-1",
                text="Built REST API endpoints using Python and FastAPI serving 5k requests/sec",
                source_bullet_ids=["b-1"],
                validation_status="needs_confirmation",
            ),
        ]
        report = validate_claims(bullets, profile)
        assert report.status == "passed"
        assert report.summary.supported_claims == 1


class TestDeterministicRewrite:
    def test_preserves_original_text(self):
        bullets = [
            Bullet(id="b-1", text="Built an API in Python", skills=["Python"], approved=True),
            Bullet(id="b-2", text="Deployed with Docker", skills=["Docker"], approved=True),
        ]
        result = rewrite_bullets_deterministic(bullets, jd_skills=["Python", "Docker"])
        assert len(result) == 2
        assert result[0].text == "Built an API in Python"
        assert result[0].validation_status == "supported"
        assert result[1].text == "Deployed with Docker"

    def test_all_bullets_marked_supported(self):
        bullets = [
            Bullet(id="b-1", text="Some work", skills=[], approved=True),
        ]
        result = rewrite_bullets_deterministic(bullets, jd_skills=[])
        assert all(b.validation_status == "supported" for b in result)


class TestRewriteWithMockProvider:
    async def test_llm_rewrite_returns_generated_bullets(self):
        provider = MockProvider(
            responses=[
                [
                    {
                        "source_bullet_id": "b-1",
                        "text": "Developed a high-performance API",
                        "jd_keywords_used": ["Python"],
                        "validation_notes": ["Improved action verb"],
                    }
                ]
            ]
        )
        bullets = [
            Bullet(id="b-1", text="Built an API", skills=["Python"], approved=True),
        ]
        result = await rewrite_bullets(
            bullets,
            jd_skills=["Python"],
            jd_responsibilities=["Build APIs"],
            provider=provider,
        )
        assert len(result) == 1
        assert result[0].text == "Developed a high-performance API"
        assert result[0].validation_status == "needs_confirmation"

    async def test_fallback_on_provider_error(self):
        provider = MockProvider()
        provider.add_error("LLM unavailable")
        bullets = [
            Bullet(id="b-1", text="Built an API", skills=["Python"], approved=True),
        ]
        result = await rewrite_bullets(
            bullets,
            jd_skills=["Python"],
            jd_responsibilities=[],
            provider=provider,
        )
        assert len(result) == 1
        assert result[0].text == "Built an API"
        assert result[0].validation_status == "supported"

    async def test_missing_bullets_added_back(self):
        """If LLM only rewrites some bullets, the rest are added back."""
        provider = MockProvider(
            responses=[
                [
                    {
                        "source_bullet_id": "b-1",
                        "text": "Developed an API",
                        "jd_keywords_used": [],
                        "validation_notes": ["Verb change"],
                    }
                ]
            ]
        )
        bullets = [
            Bullet(id="b-1", text="Built an API", skills=["Python"], approved=True),
            Bullet(id="b-2", text="Wrote tests", skills=["Python"], approved=True),
        ]
        result = await rewrite_bullets(
            bullets,
            jd_skills=["Python"],
            jd_responsibilities=[],
            provider=provider,
        )
        assert len(result) == 2
        source_ids = set()
        for r in result:
            source_ids.update(r.source_bullet_ids)
        assert "b-1" in source_ids
        assert "b-2" in source_ids
