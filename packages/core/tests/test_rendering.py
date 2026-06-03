"""Tests for LaTeX rendering and export — template validation."""

import zipfile
from pathlib import Path

from tailortex.rendering.exporter import (
    export_diff_report,
    export_markdown,
    export_overleaf_bundle,
    export_tex,
    export_validation_report,
)
from tailortex.rendering.latex_renderer import (
    _bold_keywords,
    _format_month_year,
    build_template_context,
    escape_latex,
    get_template_path,
    list_templates,
    render_latex,
)
from tailortex.schemas.profile import (
    Award,
    Bullet,
    CanonicalProfile,
    Certification,
    Education,
    Experience,
    Owner,
    Project,
    Publication,
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
        publications=[
            Publication(
                id="pub-1",
                title="Scalable Microservices in Python",
                venue="Journal of Software Engineering",
                date="2023-03",
                url="https://example.com/pub1",
            ),
        ],
        awards=[
            Award(
                id="award-1",
                title="Best Paper Award",
                issuer="IEEE",
                date="2023-05",
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

    def test_publications_in_context(self):
        profile = _make_full_profile()
        plan = _make_plan()
        ctx = build_template_context(profile, plan)

        assert len(ctx["publications"]) == 1
        assert ctx["publications"][0]["title"] == "Scalable Microservices in Python"
        assert ctx["publications"][0]["venue"] == "Journal of Software Engineering"
        assert ctx["publications"][0]["url"] == "https://example.com/pub1"

    def test_awards_in_context(self):
        profile = _make_full_profile()
        plan = _make_plan()
        ctx = build_template_context(profile, plan)

        assert len(ctx["awards"]) == 1
        assert ctx["awards"][0]["title"] == "Best Paper Award"
        assert ctx["awards"][0]["issuer"] == "IEEE"

    def test_publications_and_awards_empty_on_minimal(self):
        profile = _make_minimal_profile()
        plan = _make_plan()
        ctx = build_template_context(profile, plan)

        assert ctx["publications"] == []
        assert ctx["awards"] == []

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
        assert "Jan 2022" in ctx["experience"][0]["dates"]
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

    def test_publications_rendered(self):
        profile = _make_full_profile()
        plan = _make_plan()
        tex = render_latex(profile, plan)
        assert "Scalable Microservices in Python" in tex
        assert "Journal of Software Engineering" in tex

    def test_awards_rendered(self):
        profile = _make_full_profile()
        plan = _make_plan()
        tex = render_latex(profile, plan)
        assert "Best Paper Award" in tex
        assert "IEEE" in tex


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
        assert "| Supported | 3 |" in content

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


class TestFormatMonthYear:
    def test_formats_january(self):
        assert _format_month_year("2022-01") == "Jan 2022"

    def test_formats_december(self):
        assert _format_month_year("2023-12") == "Dec 2023"

    def test_empty_string(self):
        assert _format_month_year("") == ""

    def test_invalid_format(self):
        assert _format_month_year("not-a-date") == "a-date not"

    def test_unknown_month(self):
        assert _format_month_year("2022-13") == "13 2022"


class TestTemplateDiscovery:
    def test_ats_modern_found(self):
        templates = list_templates()
        assert "ats-modern" in templates

    def test_classic_found(self):
        templates = list_templates()
        assert "classic" in templates

    def test_ats_modern_path(self):
        path = get_template_path("ats-modern")
        assert path.exists()
        assert path.name == "main.tex.j2"

    def test_classic_path(self):
        path = get_template_path("classic")
        assert path.exists()
        assert path.name == "main.tex.j2"

    def test_unknown_template_raises(self):
        import pytest
        with pytest.raises(FileNotFoundError):
            get_template_path("nonexistent")

    def test_template_metadata(self):
        templates = list_templates()
        assert templates["ats-modern"]["id"] == "ats-modern"
        assert templates["classic"]["id"] == "classic"
        assert "description" in templates["classic"]


class TestRenderClassicTemplate:
    def test_renders_full_profile(self):
        profile = _make_full_profile()
        plan = _make_plan()
        tex = render_latex(profile, plan, template_id="classic")

        assert r"\documentclass" in tex
        assert "Jane Doe" in tex
        assert r"\section{Professional Experience}" in tex

    def test_dates_formatted(self):
        profile = _make_full_profile()
        plan = _make_plan()
        tex = render_latex(profile, plan, template_id="classic")

        assert "Jan 2022" in tex
        assert "Present" in tex

    def test_publications_rendered(self):
        profile = _make_full_profile()
        plan = _make_plan()
        tex = render_latex(profile, plan, template_id="classic")
        assert "Scalable Microservices in Python" in tex
        assert "Journal of Software Engineering" in tex

    def test_awards_rendered(self):
        profile = _make_full_profile()
        plan = _make_plan()
        tex = render_latex(profile, plan, template_id="classic")
        assert "Best Paper Award" in tex
        assert "IEEE" in tex


class TestExportMarkdown:
    def test_creates_markdown_file(self, tmp_path: Path):
        profile = _make_full_profile()
        plan = _make_plan()
        out = tmp_path / "resume.md"

        result = export_markdown(profile, plan, out)

        assert result.exists()
        content = result.read_text()
        assert "# Jane Doe" in content
        assert "jane@example.com" in content

    def test_includes_all_sections(self, tmp_path: Path):
        profile = _make_full_profile()
        plan = _make_plan()
        out = tmp_path / "resume.md"

        result = export_markdown(profile, plan, out)
        content = result.read_text()

        assert "## Summary" in content
        assert "## Skills" in content
        assert "## Experience" in content
        assert "## Projects" in content
        assert "## Education" in content
        assert "## Certifications" in content

    def test_no_empty_sections(self, tmp_path: Path):
        profile = _make_minimal_profile()
        plan = _make_plan()
        out = tmp_path / "resume.md"

        result = export_markdown(profile, plan, out)
        content = result.read_text()

        assert "## Summary" not in content
        assert "## Skills" not in content
        assert "## Experience" not in content
        assert "## Projects" not in content
        assert "## Education" not in content
        assert "## Certifications" not in content

    def test_contact_info_rendered(self, tmp_path: Path):
        profile = _make_full_profile()
        plan = _make_plan()
        out = tmp_path / "resume.md"

        result = export_markdown(profile, plan, out)
        content = result.read_text()

        assert "555-123-4567" in content
        assert "Austin, TX" in content

    def test_experience_details(self, tmp_path: Path):
        profile = _make_full_profile()
        plan = _make_plan()
        out = tmp_path / "resume.md"

        result = export_markdown(profile, plan, out)
        content = result.read_text()

        assert "Senior Software Engineer" in content
        assert "Acme Corp" in content
        assert "Built REST APIs" in content

    def test_skills_grouped(self, tmp_path: Path):
        profile = _make_full_profile()
        plan = _make_plan()
        out = tmp_path / "resume.md"

        result = export_markdown(profile, plan, out)
        content = result.read_text()

        assert "Languages" in content
        assert "Python" in content
        assert "Frameworks" in content
        assert "FastAPI" in content

    def test_certifications_included(self, tmp_path: Path):
        profile = _make_full_profile()
        plan = _make_plan()
        out = tmp_path / "resume.md"

        result = export_markdown(profile, plan, out)
        content = result.read_text()

        assert "AWS Solutions Architect" in content
        assert "Amazon" in content

    def test_projects_included(self, tmp_path: Path):
        profile = _make_full_profile()
        plan = _make_plan()
        out = tmp_path / "resume.md"

        result = export_markdown(profile, plan, out)
        content = result.read_text()

        assert "LogPipe" in content
        assert "Log aggregation tool" in content

    def test_education_included(self, tmp_path: Path):
        profile = _make_full_profile()
        plan = _make_plan()
        out = tmp_path / "resume.md"

        result = export_markdown(profile, plan, out)
        content = result.read_text()

        assert "UT Austin" in content
        assert "B.S." in content
        assert "Computer Science" in content

    def test_publications_included(self, tmp_path: Path):
        profile = _make_full_profile()
        plan = _make_plan()
        out = tmp_path / "resume.md"

        result = export_markdown(profile, plan, out)
        content = result.read_text()

        assert "## Selected Publications" in content
        assert "Scalable Microservices in Python" in content
        assert "Journal of Software Engineering" in content

    def test_awards_included(self, tmp_path: Path):
        profile = _make_full_profile()
        plan = _make_plan()
        out = tmp_path / "resume.md"

        result = export_markdown(profile, plan, out)
        content = result.read_text()

        assert "## Honors & Awards" in content
        assert "Best Paper Award" in content
        assert "IEEE" in content

    def test_no_publications_or_awards_on_minimal(self, tmp_path: Path):
        profile = _make_minimal_profile()
        plan = _make_plan()
        out = tmp_path / "resume.md"

        result = export_markdown(profile, plan, out)
        content = result.read_text()

        assert "## Selected Publications" not in content
        assert "## Honors & Awards" not in content

    def test_generated_bullets_override(self, tmp_path: Path):
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
        out = tmp_path / "resume.md"

        result = export_markdown(profile, plan, out, generated_bullets=gen)
        content = result.read_text()

        assert "Improved REST APIs with Python" in content

    def test_latex_special_chars_not_escaped(self, tmp_path: Path):
        profile = _make_full_profile()
        profile.owner.full_name = "Jane & John"
        plan = _make_plan()
        out = tmp_path / "resume.md"

        result = export_markdown(profile, plan, out)
        content = result.read_text()

        assert "Jane & John" in content
        assert "\\&" not in content


class TestLongSkillLists:
    def test_long_skill_lists_dont_break_template(self):
        profile = CanonicalProfile(
            owner=Owner(full_name="Skill Heavy User", email="skills@example.com"),
            skills=[
                Skill(name=f"Skill{chr(65 + i // 5)}{i % 5}", category=cat)
                for i, cat in enumerate(
                    [
                        "Languages",
                        "Languages",
                        "Languages",
                        "Languages",
                        "Languages",
                        "Frameworks",
                        "Frameworks",
                        "Frameworks",
                        "Frameworks",
                        "Frameworks",
                        "Tools",
                        "Tools",
                        "Tools",
                        "Tools",
                        "Tools",
                        "Databases",
                        "Databases",
                        "Databases",
                        "Databases",
                        "Databases",
                        "DevOps",
                        "DevOps",
                        "DevOps",
                        "DevOps",
                        "DevOps",
                        "Testing",
                        "Testing",
                        "Testing",
                        "Testing",
                        "Testing",
                        "Concepts",
                        "Concepts",
                        "Concepts",
                        "Concepts",
                        "Concepts",
                        "Cloud",
                        "Cloud",
                        "Cloud",
                        "Cloud",
                        "Cloud",
                    ]
                )
            ],
        )
        plan = _make_plan()
        tex = render_latex(profile, plan)

        assert "None" not in tex
        assert "null" not in tex
        assert "SkillA0" in tex
        assert "SkillG4" in tex
        assert r"\section{Technical Skills}" in tex

    def test_template_renders_with_publications(self):
        from tailortex.schemas.profile import Publication

        profile = CanonicalProfile(
            owner=Owner(full_name="Pub Author", email="author@example.com"),
            publications=[
                Publication(
                    id="pub-1",
                    title="Advances in Machine Learning",
                    venue="NeurIPS 2025",
                    date="2025-12",
                ),
                Publication(
                    id="pub-2",
                    title="Distributed Systems at Scale",
                    venue="OSDI 2024",
                    date="2024-07",
                ),
            ],
        )
        plan = _make_plan()
        tex = render_latex(profile, plan)

        assert r"\section{Publications}" in tex
        assert "Advances in Machine Learning" in tex
        assert "NeurIPS 2025" in tex
        assert "Distributed Systems at Scale" in tex
        assert "OSDI 2024" in tex
        assert "None" not in tex

    def test_template_renders_with_awards(self):
        from tailortex.schemas.profile import Award

        profile = CanonicalProfile(
            owner=Owner(full_name="Award Winner", email="winner@example.com"),
            awards=[
                Award(
                    id="award-1",
                    title="Best Paper Award",
                    issuer="ACM SIGPLAN",
                    date="2024-06",
                ),
                Award(
                    id="award-2",
                    title="Engineering Excellence",
                    issuer="CompanyX",
                    date="2023-11",
                ),
            ],
        )
        plan = _make_plan()
        tex = render_latex(profile, plan)

        assert r"\section{Awards}" in tex
        assert "Best Paper Award" in tex
        assert "ACM SIGPLAN" in tex
        assert "Engineering Excellence" in tex
        assert "CompanyX" in tex
        assert "None" not in tex
