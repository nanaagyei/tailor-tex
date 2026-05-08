"""Tests for LaTeX rendering and export — template validation."""

import zipfile
from pathlib import Path

from tailortex.rendering.exporter import (
    export_diff_report,
    export_overleaf_bundle,
    export_tex,
    export_validation_report,
)
from tailortex.rendering.latex_renderer import (
    _bold_keywords,
    build_template_context,
    escape_latex,
    render_latex,
)
from tailortex.schemas.profile import (
    Bullet,
    CanonicalProfile,
    Certification,
    Education,
    Experience,
    Owner,
    Project,
    Skill,
    Summary,
)
from tailortex.schemas.resume import GeneratedBullet, ResumePlan
from tailortex.schemas.validation import ClaimResult, ValidationReport, ValidationSummary, Warning


def _make_full_profile() -> CanonicalProfile:
    """Profile with all sections populated."""
    return CanonicalProfile(
        owner=Owner(
            full_name="Jane Doe",
            email="jane@example.com",
            phone="555-123-4567",
            location="Austin, TX",
        ),
        summary=Summary(
            source_text="Experienced software engineer with 5 years in backend systems."
        ),
        experiences=[
            Experience(
                id="exp-1",
                organization="Acme Corp",
                title="Senior Software Engineer",
                start_date="2022-01",
                is_current=True,
                approved=True,
                bullets=[
                    Bullet(
                        id="b-1",
                        text="Built REST APIs using Python & FastAPI serving 5k req/sec",
                        skills=["Python", "FastAPI"],
                        approved=True,
                        metrics=["5k req/sec"],
                    ),
                    Bullet(
                        id="b-2",
                        text="Deployed services with Docker & CI/CD pipelines",
                        skills=["Docker", "CI/CD"],
                        approved=True,
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
                        text="Processing 100k events/day with 99.9% uptime",
                        skills=["Python"],
                        approved=True,
                        metrics=["100k events/day"],
                    ),
                ],
            ),
        ],
        skills=[
            Skill(name="Python", category="Languages"),
            Skill(name="FastAPI", category="Frameworks"),
            Skill(name="Docker", category="Tools"),
            Skill(name="PostgreSQL", category="Databases"),
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
        certifications=[
            Certification(
                id="cert-1",
                name="AWS Solutions Architect",
                issuer="Amazon",
                date="2023-06",
            ),
        ],
    )


def _make_minimal_profile() -> CanonicalProfile:
    """Profile with only required fields."""
    return CanonicalProfile(
        owner=Owner(full_name="Min User", email="min@example.com"),
    )


def _make_plan() -> ResumePlan:
    return ResumePlan(
        resume_id="resume-1",
        target_job_id="job-1",
        template_id="ats-modern",
    )


class TestEscapeLatex:
    def test_escapes_ampersand(self):
        assert escape_latex("R&D") == r"R\&D"

    def test_escapes_percent(self):
        assert escape_latex("50%") == r"50\%"

    def test_escapes_dollar(self):
        assert escape_latex("$100") == r"\$100"

    def test_escapes_hash(self):
        assert escape_latex("C#") == r"C\#"

    def test_escapes_underscore(self):
        assert escape_latex("my_var") == r"my\_var"

    def test_escapes_braces(self):
        assert escape_latex("{test}") == r"\{test\}"

    def test_escapes_tilde(self):
        assert escape_latex("~user") == r"\textasciitilde{}user"

    def test_escapes_caret(self):
        assert escape_latex("x^2") == r"x\textasciicircum{}2"

    def test_escapes_backslash(self):
        assert escape_latex("a\\b") == r"a\textbackslash{}b"

    def test_plain_text_unchanged(self):
        assert escape_latex("Hello World") == "Hello World"

    def test_multiple_specials(self):
        result = escape_latex("R&D costs $50 (100%)")
        assert r"\&" in result
        assert r"\$" in result
        assert r"\%" in result


class TestBoldKeywords:
    def test_bold_single_keyword(self):
        result = _bold_keywords("Built REST APIs with Python", ["Python"])
        assert r"\textbf{Python}" in result

    def test_bold_max_three(self):
        result = _bold_keywords(
            "Used Python, FastAPI, Docker, PostgreSQL",
            ["Python", "FastAPI", "Docker", "PostgreSQL"],
        )
        bold_count = result.count(r"\textbf{")
        assert bold_count == 3

    def test_no_keywords(self):
        text = "Built an API"
        assert _bold_keywords(text, []) == text

    def test_keyword_not_found(self):
        text = "Built an API"
        assert _bold_keywords(text, ["Kubernetes"]) == text


class TestBuildTemplateContext:
    def test_full_profile_has_all_sections(self):
        profile = _make_full_profile()
        plan = _make_plan()
        ctx = build_template_context(profile, plan)

        assert ctx["name"] == "Jane Doe"
        assert ctx["contact"]["email"] == "jane@example.com"
        assert ctx["summary"]
        assert len(ctx["skills"]) > 0
        assert len(ctx["experience"]) > 0
        assert len(ctx["projects"]) > 0
        assert len(ctx["education"]) > 0
        assert len(ctx["certifications"]) > 0

    def test_minimal_profile_has_empty_sections(self):
        profile = _make_minimal_profile()
        plan = _make_plan()
        ctx = build_template_context(profile, plan)

        assert ctx["name"] == "Min User"
        assert ctx["summary"] == ""
        assert ctx["experience"] == []
        assert ctx["projects"] == []
        assert ctx["certifications"] == []

    def test_generated_bullets_override_originals(self):
        profile = _make_full_profile()
        plan = _make_plan()
        gen = [
            GeneratedBullet(
                id="gen-1",
                text="Improved REST APIs with Python and FastAPI",
                source_bullet_ids=["b-1"],
                validation_status="supported",
            ),
        ]
        ctx = build_template_context(profile, plan, generated_bullets=gen)
        # The first experience bullet should use the generated text
        exp_bullets = ctx["experience"][0]["bullets"]
        assert any("Improved" in b for b in exp_bullets)

    def test_rejected_bullets_excluded(self):
        profile = _make_full_profile()
        plan = _make_plan()
        gen = [
            GeneratedBullet(
                id="gen-1",
                text="Fabricated claim about Kubernetes",
                source_bullet_ids=["b-1"],
                validation_status="rejected",
            ),
        ]
        ctx = build_template_context(profile, plan, generated_bullets=gen)
        # Rejected bullet should NOT override — original text used
        exp_bullets = ctx["experience"][0]["bullets"]
        assert not any("Fabricated" in b for b in exp_bullets)

    def test_special_chars_escaped_in_context(self):
        profile = _make_full_profile()
        # Modify to include special chars
        profile.owner.full_name = "Jane & John"
        plan = _make_plan()
        ctx = build_template_context(profile, plan)
        assert r"\&" in ctx["name"]

    def test_experience_dates_format(self):
        profile = _make_full_profile()
        plan = _make_plan()
        ctx = build_template_context(profile, plan)
        # Current role should show "Present"
        assert "Present" in ctx["experience"][0]["dates"]


class TestRenderLatex:
    def test_renders_full_profile(self):
        profile = _make_full_profile()
        plan = _make_plan()
        tex = render_latex(profile, plan)

        assert r"\documentclass" in tex
        assert "Jane Doe" in tex
        assert r"\section{Professional Experience}" in tex
        assert r"\section{Education}" in tex
        assert r"\section{Technical Skills}" in tex

    def test_renders_minimal_profile(self):
        profile = _make_minimal_profile()
        plan = _make_plan()
        tex = render_latex(profile, plan)

        assert r"\documentclass" in tex
        assert "Min User" in tex
        # Empty sections should not appear
        assert r"\section{Professional Experience}" not in tex
        assert r"\section{Selected Projects}" not in tex

    def test_no_none_or_null_in_output(self):
        profile = _make_full_profile()
        plan = _make_plan()
        tex = render_latex(profile, plan)

        assert "None" not in tex
        assert "null" not in tex

    def test_special_chars_escaped(self):
        profile = _make_full_profile()
        plan = _make_plan()
        tex = render_latex(profile, plan)

        # The & in "Python & FastAPI" should be escaped
        assert r"\&" in tex

    def test_certifications_rendered(self):
        profile = _make_full_profile()
        plan = _make_plan()
        tex = render_latex(profile, plan)
        assert "AWS Solutions Architect" in tex

    def test_summary_rendered(self):
        profile = _make_full_profile()
        plan = _make_plan()
        tex = render_latex(profile, plan)
        assert r"\section{Summary}" in tex
        assert "Experienced software engineer" in tex


class TestExportTex:
    def test_creates_tex_file(self, tmp_path: Path):
        profile = _make_full_profile()
        plan = _make_plan()
        out = tmp_path / "resume.tex"

        result = export_tex(profile, plan, out)

        assert result.exists()
        content = result.read_text()
        assert r"\documentclass" in content

    def test_creates_parent_dirs(self, tmp_path: Path):
        profile = _make_full_profile()
        plan = _make_plan()
        out = tmp_path / "nested" / "dir" / "resume.tex"

        result = export_tex(profile, plan, out)
        assert result.exists()


class TestExportOverleafBundle:
    def test_creates_zip(self, tmp_path: Path):
        profile = _make_full_profile()
        plan = _make_plan()
        out = tmp_path / "bundle.zip"

        result = export_overleaf_bundle(profile, plan, out)

        assert result.exists()
        with zipfile.ZipFile(result) as zf:
            names = zf.namelist()
            assert "main.tex" in names
            assert "README.md" in names

    def test_zip_contains_valid_tex(self, tmp_path: Path):
        profile = _make_full_profile()
        plan = _make_plan()
        out = tmp_path / "bundle.zip"

        export_overleaf_bundle(profile, plan, out)

        with zipfile.ZipFile(out) as zf:
            tex = zf.read("main.tex").decode()
            assert r"\documentclass" in tex
            assert "Jane Doe" in tex

    def test_no_private_metadata_in_bundle(self, tmp_path: Path):
        profile = _make_full_profile()
        plan = _make_plan()
        out = tmp_path / "bundle.zip"

        export_overleaf_bundle(profile, plan, out)

        with zipfile.ZipFile(out) as zf:
            names = zf.namelist()
            # Should only contain main.tex and README.md
            assert len(names) == 2


class TestExportValidationReport:
    def test_creates_markdown(self, tmp_path: Path):
        report = ValidationReport(
            resume_id="r-1",
            status="passed",
            summary=ValidationSummary(supported_claims=3),
            claims=[
                ClaimResult(claim="Built APIs", status="supported"),
            ],
        )
        out = tmp_path / "report.md"

        result = export_validation_report(report, out)

        assert result.exists()
        content = result.read_text()
        assert "# Validation Report" in content
        assert "passed" in content
        assert "Supported: 3" in content

    def test_includes_warnings(self, tmp_path: Path):
        report = ValidationReport(
            resume_id="r-1",
            status="failed",
            summary=ValidationSummary(rejected_claims=1, warnings=1),
            warnings=[
                Warning(type="REJECTED_CLAIM", message="Kubernetes fabricated"),
            ],
        )
        out = tmp_path / "report.md"

        result = export_validation_report(report, out)
        content = result.read_text()
        assert "REJECTED_CLAIM" in content
        assert "Kubernetes fabricated" in content


class TestExportDiffReport:
    def test_creates_diff_markdown(self, tmp_path: Path):
        originals = ["Built an API", "Deployed services"]
        generated = [
            GeneratedBullet(
                id="gen-1",
                text="Developed a high-performance API",
                source_bullet_ids=["b-1"],
                validation_status="supported",
            ),
        ]
        out = tmp_path / "diff.md"

        result = export_diff_report(originals, generated, out)

        assert result.exists()
        content = result.read_text()
        assert "# Diff Report" in content
        assert "Built an API" in content
        assert "Developed a high-performance API" in content
