"""Comprehensive CLI tests for TailorTex."""

import json
import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from tailortex_cli.main import (
    EXIT_GENERAL,
    EXIT_PARSER,
    EXIT_PRIVACY,
    EXIT_PROVIDER,
    EXIT_RENDER,
    EXIT_SUCCESS,
    EXIT_VALIDATION,
    app,
)


# ── Test data ────────────────────────────────────────────────

SAMPLE_RESUME = (
    "Morgan Castillo\n"
    "morgan.castillo@proton.me | (512) 847-1928\n"
    "Austin, TX\n"
    "https://github.com/mcastillo-dev | https://linkedin.com/in/mcastillo\n"
    "\n"
    "Summary\n"
    "Software engineer with 4 years of experience building backend services, "
    "testing infrastructure, and developer tooling.\n"
    "\n"
    "Experience\n"
    "\n"
    "Software Engineer | Meridian Systems\n"
    "Austin, TX\n"
    "Mar 2023 - Present\n"
    "- Designed and maintained CI/CD pipelines using GitHub Actions, "
    "reducing deploy time by 40%\n"
    "- Built REST API endpoints in Python (FastAPI) serving 2M+ requests/day\n"
)

SAMPLE_JD = (
    "Senior Backend Engineer\n\n"
    "We are looking for a Senior Backend Engineer to join our team. "
    "Required skills: Python, Docker, REST APIs, PostgreSQL. "
    "Experience with CI/CD pipelines and microservices preferred. "
    "You will design and maintain backend services and APIs.\n"
)


def _make_approved_profile_json() -> str:
    """Construct a CanonicalProfile JSON with approved=True on experiences."""
    return json.dumps(
        {
            "profile_id": "default",
            "version": "1.0.0",
            "owner": {
                "full_name": "Morgan Castillo",
                "email": "morgan.castillo@proton.me",
                "phone": "(512) 847-1928",
                "location": "Austin, TX",
                "links": [
                    {"label": "GitHub", "url": "https://github.com/mcastillo-dev"},
                    {"label": "LinkedIn", "url": "https://linkedin.com/in/mcastillo"},
                ],
            },
            "summary": {
                "source_text": (
                    "Software engineer with 4 years of experience building "
                    "backend services, testing infrastructure, and developer tooling."
                ),
                "approved": True,
            },
            "experiences": [
                {
                    "id": "exp_test1",
                    "organization": "Meridian Systems",
                    "title": "Software Engineer",
                    "location": "Austin, TX",
                    "start_date": "2023-03",
                    "is_current": True,
                    "approved": True,
                    "bullets": [
                        {
                            "id": "b1",
                            "text": (
                                "Designed and maintained CI/CD pipelines using "
                                "GitHub Actions, reducing deploy time by 40%"
                            ),
                            "skills": ["CI/CD", "GitHub Actions"],
                            "approved": True,
                        },
                        {
                            "id": "b2",
                            "text": (
                                "Built REST API endpoints in Python (FastAPI) "
                                "serving 2M+ requests/day"
                            ),
                            "skills": ["Python", "FastAPI", "REST APIs"],
                            "approved": True,
                        },
                    ],
                }
            ],
            "education": [],
            "projects": [],
            "skills": [],
            "evidence_ledger": [],
        }
    )


def _make_unapproved_profile_json() -> str:
    """Profile JSON where no experiences/education/projects are approved."""
    return json.dumps(
        {
            "profile_id": "default",
            "version": "1.0.0",
            "owner": {
                "full_name": "Morgan Castillo",
                "email": "morgan.castillo@proton.me",
                "phone": "(512) 847-1928",
                "location": "Austin, TX",
                "links": [
                    {"label": "GitHub", "url": "https://github.com/mcastillo-dev"},
                ],
            },
            "experiences": [
                {
                    "id": "exp_raw1",
                    "organization": "Meridian Systems",
                    "title": "Software Engineer",
                    "start_date": "2023-03",
                    "is_current": True,
                    "approved": False,
                    "bullets": [
                        {"id": "b1", "text": "Built CI/CD pipelines.", "approved": False},
                        {"id": "b2", "text": "Built REST APIs.", "approved": False},
                    ],
                }
            ],
            "education": [],
            "projects": [],
            "skills": [],
            "evidence_ledger": [],
        }
    )


# ── Fixtures ──────────────────────────────────────────────


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def workspace_dir() -> Path:
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def resume_file(workspace_dir: Path) -> Path:
    path = workspace_dir / "resume.txt"
    path.write_text(SAMPLE_RESUME)
    return path


@pytest.fixture
def jd_file(workspace_dir: Path) -> Path:
    path = workspace_dir / "jd.txt"
    path.write_text(SAMPLE_JD)
    return path


@pytest.fixture
def approved_profile_file(workspace_dir: Path) -> Path:
    path = workspace_dir / "approved_profile.json"
    path.write_text(_make_approved_profile_json())
    return path


@pytest.fixture
def unapproved_profile_file(workspace_dir: Path) -> Path:
    path = workspace_dir / "unapproved_profile.json"
    path.write_text(_make_unapproved_profile_json())
    return path


@pytest.fixture
def invalid_json_file(workspace_dir: Path) -> Path:
    path = workspace_dir / "bad.json"
    path.write_text("{invalid: json, content")
    return path


@pytest.fixture
def initialised_workspace(runner: CliRunner, workspace_dir: Path) -> Path:
    """Workspace that has been initialised and has an imported resume."""
    ws = workspace_dir / ".ws"
    runner.invoke(app, ["init", "--workspace", str(ws)])
    runner.invoke(
        app,
        ["import", str(workspace_dir / "resume.txt"), "--workspace", str(ws)],
    )
    return ws


def _ws_flag(workspace_dir: Path) -> list[str]:
    """Build --workspace flag pointing into a tempdir root."""
    return ["--workspace", str(workspace_dir / ".ws")]


# ── Test: version ────────────────────────────────────────


class TestVersion:
    def test_outputs_version_string(self, runner: CliRunner) -> None:
        result = runner.invoke(app, ["version"])
        assert result.exit_code == EXIT_SUCCESS
        assert "tailortex" in result.stdout


# ── Test: init ───────────────────────────────────────────


class TestInit:
    def test_creates_workspace_dir(self, runner: CliRunner, workspace_dir: Path) -> None:
        ws = workspace_dir / ".ws"
        result = runner.invoke(app, ["init", "--workspace", str(ws)])
        assert result.exit_code == EXIT_SUCCESS
        assert ws.is_dir()
        assert "Workspace created" in result.stdout

    def test_existing_workspace_shows_message(
        self, runner: CliRunner, workspace_dir: Path
    ) -> None:
        ws = workspace_dir / ".ws"
        runner.invoke(app, ["init", "--workspace", str(ws)])
        result = runner.invoke(app, ["init", "--workspace", str(ws)])
        assert result.exit_code == EXIT_SUCCESS
        assert "already exists" in result.stdout


# ── Test: import ─────────────────────────────────────────


class TestImport:
    def test_imports_resume_file(
        self, runner: CliRunner, workspace_dir: Path, resume_file: Path
    ) -> None:
        ws = workspace_dir / ".ws"
        result = runner.invoke(
            app, ["import", str(resume_file), "--workspace", str(ws)]
        )
        assert result.exit_code == EXIT_SUCCESS
        assert "Imported" in result.stdout
        assert "Profile draft saved" in result.stdout

    def test_nonexistent_file_shows_error(
        self, runner: CliRunner, workspace_dir: Path
    ) -> None:
        ws = workspace_dir / ".ws"
        result = runner.invoke(
            app, ["import", "/nonexistent/path/file.txt", "--workspace", str(ws)]
        )
        assert result.exit_code == EXIT_PARSER


# ── Test: profile review ─────────────────────────────────


class TestProfileReview:
    def test_reviews_default_profile(
        self, runner: CliRunner, workspace_dir: Path, approved_profile_file: Path
    ) -> None:
        """Review an approved profile."""
        ws = workspace_dir / ".ws"
        runner.invoke(app, ["init", "--workspace", str(ws)])
        runner.invoke(
            app,
            ["profile", "approve", str(approved_profile_file), "--workspace", str(ws)],
        )
        result = runner.invoke(
            app, ["profile", "review", "--workspace", str(ws)]
        )
        assert result.exit_code == EXIT_SUCCESS
        assert "Morgan Castillo" in result.stdout

    def test_no_workspace_shows_error(self, runner: CliRunner, workspace_dir: Path) -> None:
        ws = workspace_dir / ".nonexistent"
        result = runner.invoke(
            app, ["profile", "review", "--workspace", str(ws)]
        )
        assert result.exit_code == EXIT_GENERAL


# ── Test: profile approve ────────────────────────────────


class TestProfileApprove:
    def test_approves_valid_json(
        self, runner: CliRunner, workspace_dir: Path, approved_profile_file: Path
    ) -> None:
        ws = workspace_dir / ".ws"
        runner.invoke(app, ["init", "--workspace", str(ws)])
        result = runner.invoke(
            app,
            ["profile", "approve", str(approved_profile_file), "--workspace", str(ws)],
        )
        assert result.exit_code == EXIT_SUCCESS
        assert "Profile approved" in result.stdout

    def test_rejects_invalid_json(
        self, runner: CliRunner, workspace_dir: Path, invalid_json_file: Path
    ) -> None:
        ws = workspace_dir / ".ws"
        runner.invoke(app, ["init", "--workspace", str(ws)])
        result = runner.invoke(
            app,
            ["profile", "approve", str(invalid_json_file), "--workspace", str(ws)],
        )
        assert result.exit_code == EXIT_VALIDATION

    def test_nonexistent_file_shows_error(
        self, runner: CliRunner, workspace_dir: Path
    ) -> None:
        ws = workspace_dir / ".ws"
        runner.invoke(app, ["init", "--workspace", str(ws)])
        result = runner.invoke(
            app,
            ["profile", "approve", "/nonexistent/file.json", "--workspace", str(ws)],
        )
        assert result.exit_code == EXIT_GENERAL


# ── Test: profile list ───────────────────────────────────


class TestProfileList:
    def test_lists_after_approval(
        self, runner: CliRunner, workspace_dir: Path, approved_profile_file: Path
    ) -> None:
        ws = workspace_dir / ".ws"
        runner.invoke(app, ["init", "--workspace", str(ws)])
        runner.invoke(
            app,
            ["profile", "approve", str(approved_profile_file), "--workspace", str(ws)],
        )
        result = runner.invoke(
            app, ["profile", "list", "--workspace", str(ws)]
        )
        assert result.exit_code == EXIT_SUCCESS
        assert "default" in result.stdout

    def test_empty_workspace_shows_message(
        self, runner: CliRunner, workspace_dir: Path
    ) -> None:
        ws = workspace_dir / ".ws"
        runner.invoke(app, ["init", "--workspace", str(ws)])
        result = runner.invoke(
            app, ["profile", "list", "--workspace", str(ws)]
        )
        assert result.exit_code == EXIT_SUCCESS
        assert "No profiles" in result.stdout


# ── Test: jd parse ──────────────────────────────────────


class TestJDParse:
    def test_parses_from_file(
        self, runner: CliRunner, workspace_dir: Path, jd_file: Path
    ) -> None:
        ws = workspace_dir / ".ws"
        runner.invoke(app, ["init", "--workspace", str(ws)])
        result = runner.invoke(
            app, ["jd", "parse", str(jd_file), "--workspace", str(ws)]
        )
        assert result.exit_code == EXIT_SUCCESS
        assert "Parsed Job Description" in result.stdout

    def test_parses_from_stdin(
        self, runner: CliRunner, workspace_dir: Path
    ) -> None:
        ws = workspace_dir / ".ws"
        runner.invoke(app, ["init", "--workspace", str(ws)])
        result = runner.invoke(
            app,
            ["jd", "parse", "--stdin", "--workspace", str(ws)],
            input=SAMPLE_JD,
        )
        assert result.exit_code == EXIT_SUCCESS
        assert "Parsed Job Description" in result.stdout

    def test_no_input_shows_error(
        self, runner: CliRunner, workspace_dir: Path
    ) -> None:
        ws = workspace_dir / ".ws"
        runner.invoke(app, ["init", "--workspace", str(ws)])
        result = runner.invoke(
            app, ["jd", "parse", "--workspace", str(ws)]
        )
        assert result.exit_code == EXIT_PARSER


# ── Test: tailor ─────────────────────────────────────────


class TestTailor:
    def test_fails_when_profile_not_approved(
        self, runner: CliRunner, workspace_dir: Path,
        unapproved_profile_file: Path, jd_file: Path,
    ) -> None:
        ws = workspace_dir / ".ws"
        runner.invoke(app, ["init", "--workspace", str(ws)])
        # Save a profile that exists but is not approved
        runner.invoke(
            app,
            ["profile", "approve", str(unapproved_profile_file), "--workspace", str(ws)],
        )
        result = runner.invoke(
            app,
            [
                "tailor",
                "--profile", "default",
                "--jd", str(jd_file),
                "--workspace", str(ws),
            ],
        )
        assert result.exit_code == EXIT_VALIDATION

    def test_succeeds_with_approved_profile_and_jd_file(
        self,
        runner: CliRunner,
        workspace_dir: Path,
        approved_profile_file: Path,
        jd_file: Path,
    ) -> None:
        ws = workspace_dir / ".ws"
        runner.invoke(app, ["init", "--workspace", str(ws)])
        runner.invoke(
            app,
            ["profile", "approve", str(approved_profile_file), "--workspace", str(ws)],
        )
        result = runner.invoke(
            app,
            [
                "tailor",
                "--profile", "default",
                "--jd", str(jd_file),
                "--workspace", str(ws),
            ],
        )
        assert result.exit_code == EXIT_SUCCESS
        assert "Resume exported" in result.stdout


# ── Test: export ─────────────────────────────────────────


class TestExport:
    def test_export_tex(
        self, runner: CliRunner, workspace_dir: Path, approved_profile_file: Path
    ) -> None:
        ws = workspace_dir / ".ws"
        runner.invoke(app, ["init", "--workspace", str(ws)])
        runner.invoke(
            app,
            ["profile", "approve", str(approved_profile_file), "--workspace", str(ws)],
        )
        result = runner.invoke(
            app,
            [
                "export",
                "--application", "test-app",
                "--tex",
                "--workspace", str(ws),
            ],
        )
        assert result.exit_code == EXIT_SUCCESS
        assert "TeX file" in result.stdout

    def test_export_overleaf(
        self, runner: CliRunner, workspace_dir: Path, approved_profile_file: Path
    ) -> None:
        ws = workspace_dir / ".ws"
        runner.invoke(app, ["init", "--workspace", str(ws)])
        runner.invoke(
            app,
            ["profile", "approve", str(approved_profile_file), "--workspace", str(ws)],
        )
        result = runner.invoke(
            app,
            [
                "export",
                "--application", "test-app",
                "--overleaf",
                "--workspace", str(ws),
            ],
        )
        assert result.exit_code == EXIT_SUCCESS
        assert "Overleaf bundle" in result.stdout

    def test_export_no_format_shows_message(
        self, runner: CliRunner, workspace_dir: Path, approved_profile_file: Path
    ) -> None:
        ws = workspace_dir / ".ws"
        runner.invoke(app, ["init", "--workspace", str(ws)])
        runner.invoke(
            app,
            ["profile", "approve", str(approved_profile_file), "--workspace", str(ws)],
        )
        result = runner.invoke(
            app,
            ["export", "--application", "test-app", "--workspace", str(ws)],
        )
        assert result.exit_code == EXIT_SUCCESS
        assert "Specify at least one" in result.stdout


# ── Test: validate ───────────────────────────────────────


class TestValidate:
    def test_validates_application(
        self, runner: CliRunner, workspace_dir: Path, approved_profile_file: Path
    ) -> None:
        ws = workspace_dir / ".ws"
        runner.invoke(app, ["init", "--workspace", str(ws)])
        runner.invoke(
            app,
            ["profile", "approve", str(approved_profile_file), "--workspace", str(ws)],
        )
        result = runner.invoke(
            app,
            ["validate", "--application", "test-app", "--workspace", str(ws)],
        )
        assert result.exit_code == EXIT_SUCCESS
        assert "passed" in result.stdout

    def test_no_workspace_shows_error(
        self, runner: CliRunner, workspace_dir: Path
    ) -> None:
        ws = workspace_dir / ".nonexistent"
        result = runner.invoke(
            app,
            ["validate", "--application", "test-app", "--workspace", str(ws)],
        )
        assert result.exit_code == EXIT_GENERAL


# ── Test: config ─────────────────────────────────────────


class TestConfig:
    def test_get_shows_defaults(
        self, runner: CliRunner, workspace_dir: Path
    ) -> None:
        ws = workspace_dir / ".ws"
        runner.invoke(app, ["init", "--workspace", str(ws)])
        result = runner.invoke(
            app, ["config", "get", "--workspace", str(ws)]
        )
        assert result.exit_code == EXIT_SUCCESS
        assert "version" in result.stdout

    def test_set_and_verify(
        self, runner: CliRunner, workspace_dir: Path
    ) -> None:
        ws = workspace_dir / ".ws"
        runner.invoke(app, ["init", "--workspace", str(ws)])
        set_result = runner.invoke(
            app,
            ["config", "set", "provider", "ollama", "--workspace", str(ws)],
        )
        assert set_result.exit_code == EXIT_SUCCESS
        assert "provider = ollama" in set_result.stdout

    def test_set_nested_key(
        self, runner: CliRunner, workspace_dir: Path
    ) -> None:
        ws = workspace_dir / ".ws"
        runner.invoke(app, ["init", "--workspace", str(ws)])
        result = runner.invoke(
            app,
            ["config", "set", "llm.model", "gpt-4", "--workspace", str(ws)],
        )
        assert result.exit_code == EXIT_SUCCESS
        assert "llm.model = gpt-4" in result.stdout

    def test_no_workspace_auto_inits(
        self, runner: CliRunner, workspace_dir: Path
    ) -> None:
        ws = workspace_dir / ".ws"
        result = runner.invoke(
            app, ["config", "set", "theme", "dark", "--workspace", str(ws)]
        )
        assert result.exit_code == EXIT_SUCCESS
        assert ws.is_dir()


# ── Test: workspace ──────────────────────────────────────


class TestWorkspace:
    def test_list_shows_contents(
        self, runner: CliRunner, workspace_dir: Path, approved_profile_file: Path
    ) -> None:
        ws = workspace_dir / ".ws"
        runner.invoke(app, ["init", "--workspace", str(ws)])
        runner.invoke(
            app,
            ["profile", "approve", str(approved_profile_file), "--workspace", str(ws)],
        )
        result = runner.invoke(
            app, ["workspace", "list", "--workspace", str(ws)]
        )
        assert result.exit_code == EXIT_SUCCESS
        assert str(ws) in result.stdout

    def test_info_shows_workspace_details(
        self, runner: CliRunner, workspace_dir: Path, approved_profile_file: Path
    ) -> None:
        ws = workspace_dir / ".ws"
        runner.invoke(app, ["init", "--workspace", str(ws)])
        runner.invoke(
            app,
            ["profile", "approve", str(approved_profile_file), "--workspace", str(ws)],
        )
        result = runner.invoke(
            app, ["workspace", "info", "--workspace", str(ws)]
        )
        assert result.exit_code == EXIT_SUCCESS
        assert "Workspace path" in result.stdout

    def test_info_no_workspace_shows_error(
        self, runner: CliRunner, workspace_dir: Path
    ) -> None:
        ws = workspace_dir / ".nonexistent"
        result = runner.invoke(
            app, ["workspace", "info", "--workspace", str(ws)]
        )
        assert result.exit_code == EXIT_GENERAL

    def test_delete_application(
        self, runner: CliRunner, workspace_dir: Path, approved_profile_file: Path, resume_file: Path
    ) -> None:
        ws = workspace_dir / ".ws"
        runner.invoke(app, ["init", "--workspace", str(ws)])
        runner.invoke(app, ["import", str(resume_file), "--workspace", str(ws)])
        runner.invoke(
            app,
            ["profile", "approve", str(approved_profile_file), "--workspace", str(ws)],
        )
        result = runner.invoke(
            app,
            ["workspace", "delete-application", "--force", "draft-profile", "--workspace", str(ws)],
        )
        assert result.exit_code == EXIT_SUCCESS
        assert "Deleted application" in result.stdout

    def test_delete_application_not_found(
        self, runner: CliRunner, workspace_dir: Path
    ) -> None:
        ws = workspace_dir / ".ws"
        runner.invoke(app, ["init", "--workspace", str(ws)])
        result = runner.invoke(
            app,
            ["workspace", "delete-application", "--force", "nonexistent-app", "--workspace", str(ws)],
        )
        assert result.exit_code == EXIT_GENERAL
        assert "not found" in (result.stdout.lower() + result.stderr.lower())

    def test_purge_workspace(
        self, runner: CliRunner, workspace_dir: Path, approved_profile_file: Path
    ) -> None:
        ws = workspace_dir / ".ws"
        runner.invoke(app, ["init", "--workspace", str(ws)])
        runner.invoke(
            app,
            ["profile", "approve", str(approved_profile_file), "--workspace", str(ws)],
        )
        result = runner.invoke(
            app,
            ["workspace", "purge", "--force", "--workspace", str(ws)],
        )
        assert result.exit_code == EXIT_SUCCESS
        assert "Purging workspace" in result.stdout
        assert not ws.exists()

    def test_purge_no_workspace_shows_error(
        self, runner: CliRunner, workspace_dir: Path
    ) -> None:
        ws = workspace_dir / ".nonexistent"
        result = runner.invoke(
            app, ["workspace", "purge", "--force", "--workspace", str(ws)]
        )
        assert result.exit_code == EXIT_GENERAL


# ── Test: full pipeline ──────────────────────────────────


class TestFullPipeline:
    def test_init_import_approve_jd_tailor_export(
        self,
        runner: CliRunner,
        workspace_dir: Path,
        resume_file: Path,
        approved_profile_file: Path,
        jd_file: Path,
    ) -> None:
        """End-to-end: init → import → approve → jd parse → tailor → export."""
        ws = workspace_dir / ".ws"

        # 1. Init
        r = runner.invoke(app, ["init", "--workspace", str(ws)])
        assert r.exit_code == EXIT_SUCCESS, f"init failed: {r.stdout}"
        assert ws.is_dir()

        # 2. Import resume
        r = runner.invoke(
            app, ["import", str(resume_file), "--workspace", str(ws)]
        )
        assert r.exit_code == EXIT_SUCCESS, f"import failed: {r.stdout}"

        # 3. Approve profile
        r = runner.invoke(
            app,
            ["profile", "approve", str(approved_profile_file), "--workspace", str(ws)],
        )
        assert r.exit_code == EXIT_SUCCESS, f"profile approve failed: {r.stdout}"

        # 4. Parse JD from file
        r = runner.invoke(
            app, ["jd", "parse", str(jd_file), "--workspace", str(ws)]
        )
        assert r.exit_code == EXIT_SUCCESS, f"jd parse failed: {r.stdout}"

        # 5. Tailor
        r = runner.invoke(
            app,
            [
                "tailor",
                "--profile", "default",
                "--jd", str(jd_file),
                "--mode", "conservative",
                "--template", "ats-modern",
                "--output", str(workspace_dir / "output.tex"),
                "--workspace", str(ws),
            ],
        )
        assert r.exit_code == EXIT_SUCCESS, f"tailor failed: {r.stdout}"

        # 6. Export tex
        r = runner.invoke(
            app,
            [
                "export",
                "--application", "test-app",
                "--tex",
                "--workspace", str(ws),
            ],
        )
        assert r.exit_code == EXIT_SUCCESS, f"export failed: {r.stdout}"


# ── Test: exit codes ─────────────────────────────────────


class TestExitCodes:
    def test_version_returns_success(self, runner: CliRunner) -> None:
        result = runner.invoke(app, ["version"])
        assert result.exit_code == EXIT_SUCCESS

    def test_invalid_command_returns_general(self, runner: CliRunner) -> None:
        result = runner.invoke(app, ["nonexistent-command"])
        assert result.exit_code != 0

    def test_exit_code_constants_are_distinct(self) -> None:
        codes = {
            EXIT_SUCCESS,
            EXIT_GENERAL,
            EXIT_VALIDATION,
            EXIT_PARSER,
            EXIT_PROVIDER,
            EXIT_RENDER,
            EXIT_PRIVACY,
        }
        assert len(codes) == 7


# ── Test: import saves as application not profile ────────


class TestImportSavesAsApplication:
    def test_import_creates_application_not_profile(
        self, runner: CliRunner, workspace_dir: Path, resume_file: Path
    ) -> None:
        """Fact: 'import' saves a profile draft as an application, not as a profile."""
        ws = workspace_dir / ".ws"
        runner.invoke(app, ["init", "--workspace", str(ws)])
        runner.invoke(app, ["import", str(resume_file), "--workspace", str(ws)])

        # Profile list should be empty
        r = runner.invoke(app, ["profile", "list", "--workspace", str(ws)])
        assert "No profiles" in r.stdout

        # Workspace list should show the application
        r = runner.invoke(app, ["workspace", "list", "--workspace", str(ws)])
        assert "Applications" in r.stdout
        assert "draft-profile" in r.stdout
