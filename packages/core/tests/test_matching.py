"""Tests for evidence scoring and resume selection."""

from datetime import datetime

from tailortex.matching.scorer import (
    MatchScore,
    score_experience,
    score_profile,
    score_project,
)
from tailortex.matching.selector import select_for_resume
from tailortex.schemas.job import JDSource, ParsedJobDescription, RoleSignals
from tailortex.schemas.profile import (
    Bullet,
    CanonicalProfile,
    Education,
    Experience,
    Owner,
    Project,
    Skill,
)


def _make_jd(**overrides) -> ParsedJobDescription:
    defaults = dict(
        job_id="jd-test001",
        source=JDSource(type="pasted_text"),
        company="TestCorp",
        role_title="Backend Engineer",
        required_skills=["Python", "Docker", "PostgreSQL"],
        preferred_skills=["Kubernetes", "Redis"],
        responsibilities=[
            "Design and build scalable backend services",
            "Implement REST APIs for internal consumers",
        ],
        domain_keywords=["backend", "microservices"],
        role_signals=RoleSignals(backend=0.8, frontend=0.1, leadership=0.2),
    )
    defaults.update(overrides)
    return ParsedJobDescription(**defaults)


def _make_experience(
    exp_id: str = "exp-1",
    skills: list[str] | None = None,
    start_date: str = "2023-03",
    is_current: bool = True,
    approved: bool = True,
    has_metrics: bool = True,
) -> Experience:
    bullet_skills = skills or ["Python", "Docker"]
    return Experience(
        id=exp_id,
        organization="SomeCorp",
        title="Software Engineer",
        start_date=start_date,
        is_current=is_current,
        approved=approved,
        bullets=[
            Bullet(
                id=f"{exp_id}-b1",
                text="Built scalable backend API services handling 10k requests/sec",
                skills=bullet_skills,
                approved=approved,
                metrics=["10k requests/sec"] if has_metrics else [],
            ),
            Bullet(
                id=f"{exp_id}-b2",
                text="Designed database schema and optimized query performance",
                skills=["PostgreSQL"] if "PostgreSQL" in (skills or []) else [],
                approved=approved,
                metrics=[],
            ),
        ],
    )


def _make_project(
    proj_id: str = "proj-1",
    skills: list[str] | None = None,
) -> Project:
    return Project(
        id=proj_id,
        name="TestProject",
        description="A test project",
        skills=skills or ["Python", "Docker"],
        bullets=[
            Bullet(
                id=f"{proj_id}-b1",
                text="Built a CLI tool for log analysis",
                skills=skills or ["Python"],
                approved=True,
            ),
        ],
    )


def _make_profile(
    experiences: list[Experience] | None = None,
    projects: list[Project] | None = None,
    skills: list[Skill] | None = None,
    education: list[Education] | None = None,
) -> CanonicalProfile:
    return CanonicalProfile(
        owner=Owner(full_name="Test User", email="test@example.com"),
        experiences=experiences or [],
        projects=projects or [],
        skills=skills or [Skill(name="Python"), Skill(name="Docker")],
        education=education or [],
    )


class TestScoreExperience:
    def test_returns_match_score(self):
        exp = _make_experience(skills=["Python", "Docker"])
        jd = _make_jd()
        score = score_experience(exp, jd)
        assert isinstance(score, MatchScore)
        assert score.item_type == "experience"
        assert score.item_id == "exp-1"

    def test_skill_overlap_increases_score(self):
        low = _make_experience(exp_id="low", skills=["Rust"])
        high = _make_experience(exp_id="high", skills=["Python", "Docker", "PostgreSQL"])
        jd = _make_jd()
        s_low = score_experience(low, jd)
        s_high = score_experience(high, jd)
        assert s_high.skill_score > s_low.skill_score
        assert s_high.total_score > s_low.total_score

    def test_matched_skills_listed(self):
        exp = _make_experience(skills=["Python", "Docker"])
        jd = _make_jd()
        score = score_experience(exp, jd)
        matched_lower = [s.lower() for s in score.matched_skills]
        assert "python" in matched_lower
        assert "docker" in matched_lower

    def test_current_role_gets_max_recency(self):
        exp = _make_experience(is_current=True)
        jd = _make_jd()
        score = score_experience(exp, jd)
        assert score.recency_score == 1.0

    def test_old_role_gets_low_recency(self):
        exp = _make_experience(start_date="2015-01", is_current=False)
        jd = _make_jd()
        score = score_experience(exp, jd, now=datetime(2026, 1, 1))
        assert score.recency_score <= 0.3

    def test_approved_bullets_with_metrics_score_higher(self):
        strong = _make_experience(exp_id="strong", approved=True, has_metrics=True)
        weak = _make_experience(exp_id="weak", approved=False, has_metrics=False)
        jd = _make_jd()
        s_strong = score_experience(strong, jd)
        s_weak = score_experience(weak, jd)
        assert s_strong.evidence_score > s_weak.evidence_score

    def test_alias_matching(self):
        """'k8s' in profile should match 'Kubernetes' in JD."""
        exp = _make_experience(skills=["k8s", "Python"])
        jd = _make_jd(preferred_skills=["Kubernetes"])
        score = score_experience(exp, jd)
        matched_lower = [s.lower() for s in score.matched_skills]
        assert "kubernetes" in matched_lower

    def test_scores_are_bounded(self):
        exp = _make_experience()
        jd = _make_jd()
        score = score_experience(exp, jd)
        assert 0.0 <= score.total_score <= 1.0
        assert 0.0 <= score.skill_score <= 1.0
        assert 0.0 <= score.recency_score <= 1.0
        assert 0.0 <= score.evidence_score <= 1.0


class TestScoreProject:
    def test_returns_match_score(self):
        proj = _make_project(skills=["Python"])
        jd = _make_jd()
        score = score_project(proj, jd)
        assert isinstance(score, MatchScore)
        assert score.item_type == "project"

    def test_skill_overlap(self):
        proj = _make_project(skills=["Python", "Docker", "PostgreSQL"])
        jd = _make_jd()
        score = score_project(proj, jd)
        assert score.skill_score > 0

    def test_project_has_fixed_recency(self):
        proj = _make_project()
        jd = _make_jd()
        score = score_project(proj, jd)
        assert score.recency_score == 0.3


class TestScoreProfile:
    def test_returns_sorted_scores(self):
        high_exp = _make_experience(exp_id="high", skills=["Python", "Docker", "PostgreSQL"])
        low_exp = _make_experience(exp_id="low", skills=["Rust"])
        profile = _make_profile(experiences=[low_exp, high_exp])
        jd = _make_jd()
        scores = score_profile(profile, jd)
        assert len(scores) == 2
        assert scores[0].total_score >= scores[1].total_score

    def test_includes_projects(self):
        exp = _make_experience()
        proj = _make_project()
        profile = _make_profile(experiences=[exp], projects=[proj])
        jd = _make_jd()
        scores = score_profile(profile, jd)
        types = {s.item_type for s in scores}
        assert "experience" in types
        assert "project" in types


class TestSelectForResume:
    def test_returns_resume_plan(self):
        exp = _make_experience()
        profile = _make_profile(experiences=[exp])
        jd = _make_jd()
        plan = select_for_resume(profile, jd)
        assert plan.resume_id == "resume_jd-test001"
        assert plan.target_job_id == "jd-test001"

    def test_respects_max_experiences(self):
        exps = [_make_experience(exp_id=f"exp-{i}", skills=["Python"]) for i in range(5)]
        profile = _make_profile(experiences=exps)
        jd = _make_jd()
        plan = select_for_resume(profile, jd, max_experiences=2)
        exp_sections = [s for s in plan.sections if s.type == "experience"]
        assert len(exp_sections) <= 2

    def test_respects_max_projects(self):
        projs = [_make_project(proj_id=f"proj-{i}", skills=["Python"]) for i in range(5)]
        profile = _make_profile(projects=projs)
        jd = _make_jd()
        plan = select_for_resume(profile, jd, max_projects=1)
        proj_sections = [s for s in plan.sections if s.type == "project"]
        assert len(proj_sections) <= 1

    def test_includes_education(self):
        exp = _make_experience()
        edu = Education(
            id="edu-1",
            institution="MIT",
            degree="B.S.",
            field="Computer Science",
            start_date="2017-08",
            end_date="2021-05",
        )
        profile = _make_profile(experiences=[exp], education=[edu])
        jd = _make_jd()
        plan = select_for_resume(profile, jd)
        edu_sections = [s for s in plan.sections if s.type == "education"]
        assert len(edu_sections) == 1

    def test_keyword_strategy_covered(self):
        exp = _make_experience(skills=["Python", "Docker", "PostgreSQL"])
        profile = _make_profile(
            experiences=[exp],
            skills=[Skill(name="Python"), Skill(name="Docker"), Skill(name="PostgreSQL")],
        )
        jd = _make_jd(required_skills=["Python", "Docker"], preferred_skills=[])
        plan = select_for_resume(profile, jd)
        covered_lower = [s.lower() for s in plan.keyword_strategy.covered]
        assert "python" in covered_lower
        assert "docker" in covered_lower

    def test_keyword_strategy_not_covered(self):
        exp = _make_experience(skills=["Python"])
        profile = _make_profile(
            experiences=[exp],
            skills=[Skill(name="Python")],
        )
        jd = _make_jd(required_skills=["Python", "Terraform"], preferred_skills=[])
        plan = select_for_resume(profile, jd)
        not_covered_lower = [s.lower() for s in plan.keyword_strategy.not_covered]
        assert "terraform" in not_covered_lower

    def test_do_not_insert_for_uncovered_skills(self):
        profile = _make_profile(skills=[Skill(name="Python")])
        jd = _make_jd(required_skills=["Python", "Scala"], preferred_skills=[])
        plan = select_for_resume(profile, jd)
        dni_keywords = [d.keyword.lower() for d in plan.keyword_strategy.do_not_insert]
        assert "scala" in dni_keywords

    def test_template_id_default(self):
        profile = _make_profile(experiences=[_make_experience()])
        jd = _make_jd()
        plan = select_for_resume(profile, jd)
        assert plan.template_id == "ats-modern"

    def test_template_id_custom(self):
        profile = _make_profile(experiences=[_make_experience()])
        jd = _make_jd()
        plan = select_for_resume(profile, jd, template_id="minimal")
        assert plan.template_id == "minimal"
