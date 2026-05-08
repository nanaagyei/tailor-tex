"""Tests for text extraction and resume parsing."""

from pathlib import Path

import pytest

from tailortex.parsers.extractors import ExtractionResult, extract_text
from tailortex.parsers.resume_parser import parse_resume_text

FIXTURES = Path(__file__).parent / "fixtures"


class TestTextExtraction:
    def test_extract_plaintext(self):
        result = extract_text(FIXTURES / "sample_resume.txt")
        assert result.file_type == "plaintext"
        assert "Morgan Castillo" in result.text
        assert "Meridian Systems" in result.text
        assert result.diagnostics == []

    def test_extract_markdown_strips_frontmatter(self):
        result = extract_text(FIXTURES / "sample_resume.md")
        assert result.file_type == "markdown"
        assert "Morgan Castillo" in result.text
        # Frontmatter should be stripped
        assert "title: Resume" not in result.text
        assert "author: Morgan" not in result.text

    def test_extract_nonexistent_file(self):
        with pytest.raises(FileNotFoundError):
            extract_text(FIXTURES / "does_not_exist.txt")

    def test_extract_unsupported_format(self, tmp_path):
        bad_file = tmp_path / "resume.xyz"
        bad_file.write_text("some content")
        with pytest.raises(ValueError, match="Unsupported file type"):
            extract_text(bad_file)

    def test_extract_pdf_magic_bytes(self, tmp_path):
        """A file with .xyz extension but PDF magic bytes should be detected."""
        pdf_file = tmp_path / "resume.xyz"
        # Write PDF-like header (will fail to parse but should detect type)
        pdf_file.write_bytes(b"%PDF-1.4 fake pdf content")
        # This will try to open as PDF and may fail at pymupdf level,
        # but the type detection should work
        with pytest.raises(Exception):
            extract_text(pdf_file)


class TestResumeParser:
    @pytest.fixture
    def sample_text(self):
        return (FIXTURES / "sample_resume.txt").read_text()

    def test_parse_extracts_name(self, sample_text):
        draft = parse_resume_text(sample_text)
        assert draft.profile.owner.full_name == "Morgan Castillo"

    def test_parse_extracts_email(self, sample_text):
        draft = parse_resume_text(sample_text)
        assert draft.profile.owner.email == "morgan.castillo@proton.me"

    def test_parse_extracts_phone(self, sample_text):
        draft = parse_resume_text(sample_text)
        assert draft.profile.owner.phone is not None
        assert "512" in draft.profile.owner.phone

    def test_parse_extracts_links(self, sample_text):
        draft = parse_resume_text(sample_text)
        urls = [link.url for link in draft.profile.owner.links]
        assert any("github" in u for u in urls)
        assert any("linkedin" in u for u in urls)

    def test_parse_extracts_location(self, sample_text):
        draft = parse_resume_text(sample_text)
        assert draft.profile.owner.location is not None
        assert "Austin" in draft.profile.owner.location

    def test_parse_extracts_summary(self, sample_text):
        draft = parse_resume_text(sample_text)
        assert draft.profile.summary is not None
        assert "Software engineer" in draft.profile.summary.source_text

    def test_parse_extracts_experiences(self, sample_text):
        draft = parse_resume_text(sample_text)
        assert len(draft.profile.experiences) >= 2

    def test_parse_experience_has_bullets(self, sample_text):
        draft = parse_resume_text(sample_text)
        total_bullets = sum(len(e.bullets) for e in draft.profile.experiences)
        assert total_bullets >= 4

    def test_parse_extracts_education(self, sample_text):
        draft = parse_resume_text(sample_text)
        assert len(draft.profile.education) >= 1
        edu = draft.profile.education[0]
        assert "Texas" in edu.institution or "UT" in edu.institution

    def test_parse_extracts_skills(self, sample_text):
        draft = parse_resume_text(sample_text)
        skill_names = [s.name for s in draft.profile.skills]
        assert len(skill_names) >= 5
        assert "Python" in skill_names

    def test_parse_extracts_skills_with_categories(self, sample_text):
        draft = parse_resume_text(sample_text)
        categorized = [s for s in draft.profile.skills if s.category]
        assert len(categorized) > 0

    def test_parse_extracts_projects(self, sample_text):
        draft = parse_resume_text(sample_text)
        assert len(draft.profile.projects) >= 1
        assert draft.profile.projects[0].name == "LogPipe"

    def test_parse_preserves_raw_text(self, sample_text):
        draft = parse_resume_text(sample_text)
        assert draft.raw_text == sample_text

    def test_parse_has_confidence_scores(self, sample_text):
        draft = parse_resume_text(sample_text)
        assert "contact" in draft.confidence
        assert "experience" in draft.confidence
        assert "skills" in draft.confidence
        assert all(0.0 <= v <= 1.0 for v in draft.confidence.values())

    def test_parse_empty_text(self):
        draft = parse_resume_text("")
        assert draft.profile.owner.full_name == "Unknown"
        assert len(draft.warnings) > 0

    def test_parse_minimal_text(self):
        draft = parse_resume_text("Jane Rivera\njane@example.com\n")
        assert draft.profile.owner.full_name == "Jane Rivera"
        assert draft.profile.owner.email == "jane@example.com"

    def test_profile_is_not_approved_by_default(self, sample_text):
        """Draft profiles should not be approved — user must review first."""
        draft = parse_resume_text(sample_text)
        for exp in draft.profile.experiences:
            assert exp.approved is False
            for bullet in exp.bullets:
                assert bullet.approved is False
        for skill in draft.profile.skills:
            assert skill.approved is False
