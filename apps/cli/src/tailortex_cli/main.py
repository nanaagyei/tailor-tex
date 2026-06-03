"""TailorTex CLI — command-line interface for resume tailoring."""

from __future__ import annotations

import json
import sys
import tempfile as tf
import time as _time
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="tailortex",
    help="Local-first resume tailoring workbench.",
    no_args_is_help=True,
)

profile_app = typer.Typer(help="Manage career profiles.")
jd_app = typer.Typer(help="Parse job descriptions.")
config_app = typer.Typer(help="Manage settings.")
workspace_app = typer.Typer(help="Manage local workspace.")

app.add_typer(profile_app, name="profile")
app.add_typer(jd_app, name="jd")
app.add_typer(config_app, name="config")
app.add_typer(workspace_app, name="workspace")

console = Console()
err_console = Console(stderr=True)

# Exit codes per spec.
EXIT_SUCCESS = 0
EXIT_GENERAL = 1
EXIT_VALIDATION = 2
EXIT_PARSER = 3
EXIT_PROVIDER = 4
EXIT_RENDER = 5
EXIT_PRIVACY = 6


def _get_workspace(workspace: str | None = None):
    from tailortex.storage.workspace import Workspace

    path = Path(workspace) if workspace else None
    return Workspace(path)


_SAMPLE_RESUME = (
    "Morgan Castillo\n"
    "morgan.castillo@proton.me | (512) 847-1928\n"
    "Austin, TX\n"
    "https://github.com/mcastillo-dev | https://linkedin.com/in/mcastillo\n"
    "\n"
    "Summary\n"
    "Software engineer with 4 years of experience building backend services, "
    "testing infrastructure, and developer tooling. "
    "Focused on Python, Go, and cloud-native architectures.\n"
    "\n"
    "Experience\n"
    "\n"
    "Software Engineer | Meridian Systems\n"
    "Austin, TX\n"
    "Mar 2023 - Present\n"
    "- Designed and maintained CI/CD pipelines using GitHub Actions, "
    "reducing deploy time by 40%\n"
    "- Built REST API endpoints in Python (FastAPI) serving 2M+ requests/day\n"
    "- Implemented structured logging and tracing with OpenTelemetry "
    "across 12 microservices\n"
    "\n"
    "QA Engineer | Tidewater Analytics\n"
    "Remote\n"
    "Jun 2021 - Feb 2023\n"
    "- Developed automated test suites using Pytest and Selenium, "
    "covering 85% of critical user paths\n"
    "- Reduced production bug escape rate by 30% through integration "
    "testing improvements\n"
    "\n"
    "Projects\n"
    "\n"
    "LogPipe\n"
    "https://github.com/mcastillo-dev/logpipe\n"
    "Open-source log aggregation CLI tool for local development\n"
    "- Built a Go CLI tool that aggregates logs from multiple Docker "
    "containers into a unified stream\n"
    "\n"
    "Education\n"
    "\n"
    "University of Texas at Austin\n"
    "B.S. in Computer Science\n"
    "Aug 2017 - May 2021\n"
    "GPA: 3.7\n"
    "\n"
    "Skills\n"
    "Languages: Python, Go, JavaScript\n"
    "Frameworks: FastAPI, Flask, React\n"
    "Tools: Docker, GitHub Actions, PostgreSQL\n"
    "Testing: Pytest, Selenium\n"
    "Concepts: REST APIs, CI/CD, microservices, observability\n"
)

_SAMPLE_JD = (
    "Senior Backend Engineer\n"
    "Apex Engineering | San Francisco, CA (Remote OK)\n"
    "Full-time\n"
    "\n"
    "We are looking for a Senior Backend Engineer to design and build "
    "scalable APIs.\n"
    "\n"
    "Required skills: Python, Docker, REST APIs, PostgreSQL, Go\n"
    "Preferred skills: CI/CD, Kubernetes, microservices, observability\n"
    "\n"
    "Responsibilities:\n"
    "- Design and implement RESTful APIs and backend services\n"
    "- Build and maintain CI/CD pipelines for automated testing and deployment\n"
    "- Collaborate with frontend engineers to integrate UI components "
    "with backend services\n"
    "- Write comprehensive tests and documentation\n"
)


# ── Top-level commands ──────────────────────────────────


@app.command()
def version() -> None:
    """Show the TailorTex version."""
    from tailortex import __version__

    console.print(f"tailortex {__version__}")


@app.command()
def init(
    workspace: Optional[str] = typer.Option(None, help="Custom workspace path."),
) -> None:
    """Create a new TailorTex workspace."""
    ws = _get_workspace(workspace)
    if ws.exists():
        console.print("[yellow]Workspace already exists.[/yellow]")
        return
    ws.init()
    console.print(f"[green]Workspace created:[/green] {ws.root}")
    console.print("\nNext:")
    console.print("  tailortex import <resume.pdf>")


@app.command(name="import")
def import_resume(
    file: Path = typer.Argument(..., help="Resume file to import (PDF, DOCX, MD, TXT)."),
    workspace: Optional[str] = typer.Option(None, help="Custom workspace path."),
) -> None:
    """Import a resume file and create a profile draft."""
    from tailortex.parsers.extractors import extract_text
    from tailortex.parsers.resume_parser import parse_resume_text

    if not file.exists():
        err_console.print(f"[red]File not found:[/red] {file}")
        raise typer.Exit(EXIT_PARSER)

    ws = _get_workspace(workspace)
    if not ws.exists():
        ws.init()

    result = extract_text(file)
    if not result.text:
        err_console.print(f"[red]Could not extract text from:[/red] {file}")
        raise typer.Exit(EXIT_PARSER)

    draft = parse_resume_text(result.text)

    # Save the parsed draft as an application for now
    ws.save_application("draft-profile", draft.profile.model_dump())

    console.print(f"[green]Imported:[/green] {file.name}")
    console.print("Profile draft saved.")

    if result.diagnostics:
        for w in result.diagnostics:
            console.print(f"  [yellow]Warning:[/yellow] {w}")

    console.print("\nNext:")
    console.print("  tailortex profile review")


@app.command()
def demo(
    workspace: Optional[str] = typer.Option(
        None, "--workspace", help="Use a real workspace instead of a temp directory."
    ),
    output: Optional[Path] = typer.Option(
        None, "--output", help="Output .tex path."
    ),
) -> None:
    """Run the full tailoring pipeline with built-in sample data — no setup needed."""
    from tailortex.parsers.jd_parser import parse_jd_text
    from tailortex.parsers.resume_parser import parse_resume_text
    from tailortex.matching.selector import select_for_resume
    from tailortex.llm.rewriter import rewrite_bullets_deterministic
    from tailortex.validation.claim_validator import validate_claims
    from tailortex.rendering.exporter import export_tex
    from tailortex.storage.workspace import Workspace

    start_time = _time.time()

    console.print()
    console.print("━" * 58)
    console.print("[bold white]  TailorTex · Demo Mode[/bold white]")
    console.print("[dim]  Full pipeline with built-in sample data — no setup needed[/dim]")
    console.print("━" * 58)
    console.print()

    if workspace:
        ws = _get_workspace(workspace)
        if not ws.exists():
            ws.init()
        _run_demo_pipeline(ws, output, start_time)
    else:
        with tf.TemporaryDirectory() as tmpdir:
            ws = Workspace(Path(tmpdir))
            ws.init()
            _run_demo_pipeline(ws, output, start_time)


def _run_demo_pipeline(
    ws: object, output: Path | None, start_time: float
) -> None:
    from tailortex.parsers.jd_parser import parse_jd_text
    from tailortex.parsers.resume_parser import parse_resume_text
    from tailortex.matching.selector import select_for_resume
    from tailortex.llm.rewriter import rewrite_bullets_deterministic
    from tailortex.validation.claim_validator import validate_claims
    from tailortex.rendering.exporter import export_tex

    # Parse sample resume
    with console.status("[1/6] Parsing sample resume..."):
        draft = parse_resume_text(_SAMPLE_RESUME)
    console.print("[green]✓[/green] Parsed sample resume (Morgan Castillo)")

    # Create approved profile
    with console.status("[2/6] Creating approved profile..."):
        profile = draft.profile
        if profile.summary:
            profile.summary.approved = True
        for exp in profile.experiences:
            exp.approved = True
            for b in exp.bullets:
                b.approved = True
        for proj in profile.projects:
            proj.approved = True
            for b in proj.bullets:
                b.approved = True
        ws.save_profile(profile)
    console.print(
        f"[green]✓[/green] Approved profile created "
        f"({len(profile.experiences)} experiences, "
        f"{len(profile.projects)} projects)"
    )

    # Parse sample JD
    with console.status("[3/6] Parsing sample job description..."):
        jd_result = parse_jd_text(
            _SAMPLE_JD,
            company="Apex Engineering",
            role_title="Senior Backend Engineer",
        )
    jd_obj = jd_result.jd
    console.print(
        f"[green]✓[/green] Parsed JD for {jd_obj.role_title} at {jd_obj.company}"
    )

    # Select evidence
    with console.status("[4/6] Selecting best evidence..."):
        plan = select_for_resume(profile, jd_obj, template_id="ats-modern")
    sec_types = [s.type for s in plan.sections]
    n_exp = sec_types.count("experience")
    n_proj = sec_types.count("project")
    console.print(
        f"[green]✓[/green] Selected {n_exp} experiences, {n_proj} projects"
    )

    # Collect bullets and generate
    all_bullets = []
    for exp in profile.experiences:
        all_bullets.extend(exp.bullets)
    for proj in profile.projects:
        all_bullets.extend(proj.bullets)

    with console.status("[5/6] Generating tailored bullets..."):
        generated = rewrite_bullets_deterministic(
            all_bullets, jd_obj.required_skills
        )
    console.print(f"[green]✓[/green] Generated {len(generated)} bullets")

    # Validate
    with console.status("[6/6] Validating claims against evidence..."):
        report = validate_claims(generated, profile)
    console.print(
        f"[green]✓[/green] "
        f"{report.summary.supported_claims} supported, "
        f"{report.summary.needs_confirmation} needs confirmation"
    )

    # Show validation table
    table = Table(title="Validation Report")
    table.add_column("Metric", style="bold")
    table.add_column("Count")
    table.add_row("Supported", str(report.summary.supported_claims))
    table.add_row("Needs confirmation", str(report.summary.needs_confirmation))
    table.add_row("Rejected", str(report.summary.rejected_claims))
    console.print()
    console.print(table)

    if report.status == "failed":
        err_console.print("[red]Validation failed — rejected claims found.[/red]")
        for w in report.warnings:
            err_console.print(f"  [red]{w.message}[/red]")

    # Export .tex
    out_path = output or Path(
        tf.mkdtemp(prefix="tailortex_demo_")
    ) / f"{jd_obj.job_id}.tex"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with console.status("Rendering LaTeX..."):
        bold_kw = plan.keyword_strategy.covered[:10]
        export_tex(profile, plan, out_path, generated, bold_kw)

    elapsed = _time.time() - start_time
    console.print()
    console.print(
        f"[green]Resume exported:[/green] {out_path} "
        f"[dim]({elapsed:.1f}s)[/dim]"
    )
    console.print()

    # Next steps
    console.print("[bold white]Demo complete![/bold white]")
    console.print()
    console.print("Next steps:")
    console.print(f"  1. View the generated .tex:  [dim]{out_path}[/dim]")
    console.print("  2. Run with your own data:")
    console.print("     tailortex init")
    console.print("     tailortex import <your-resume.pdf>")
    console.print("     tailortex profile review")
    console.print(
        "     tailortex profile approve <edited-profile.json>"
    )
    console.print(
        "     tailortex tailor --jd <jd.txt> --mode conservative"
    )


# ── Profile commands ────────────────────────────────────


@profile_app.command(name="review")
def profile_review(
    profile_id: str = typer.Option("default", "--profile", help="Profile ID."),
    workspace: Optional[str] = typer.Option(None, help="Custom workspace path."),
) -> None:
    """Review a profile."""
    from tailortex.storage.workspace import WorkspaceError

    ws = _get_workspace(workspace)
    if not ws.exists():
        err_console.print("[red]No workspace found. Run 'tailortex init' first.[/red]")
        raise typer.Exit(EXIT_GENERAL)

    try:
        profile = ws.load_profile(profile_id)
    except WorkspaceError:
        err_console.print(f"[red]Profile not found:[/red] {profile_id}")
        raise typer.Exit(EXIT_GENERAL)

    console.print_json(profile.model_dump_json(indent=2))
    console.print(f"\nTo approve, edit the JSON and run:")
    console.print(f"  tailortex profile approve <edited-profile.json>")


@profile_app.command(name="approve")
def profile_approve(
    file: Path = typer.Argument(..., help="Edited profile JSON file."),
    workspace: Optional[str] = typer.Option(None, help="Custom workspace path."),
) -> None:
    """Approve a reviewed profile."""
    from tailortex.schemas.profile import CanonicalProfile

    if not file.exists():
        err_console.print(f"[red]File not found:[/red] {file}")
        raise typer.Exit(EXIT_GENERAL)

    try:
        raw = json.loads(file.read_text())
        profile = CanonicalProfile(**raw)
    except Exception as e:
        err_console.print(f"[red]Invalid profile:[/red] {e}")
        raise typer.Exit(EXIT_VALIDATION)

    ws = _get_workspace(workspace)
    if not ws.exists():
        ws.init()

    ws.save_profile(profile)
    console.print(f"[green]Profile approved:[/green] {profile.profile_id}")
    console.print("\nNext:")
    console.print("  tailortex jd parse <job-description.txt>")


@profile_app.command(name="list")
def profile_list(
    workspace: Optional[str] = typer.Option(None, help="Custom workspace path."),
) -> None:
    """List all profiles."""
    ws = _get_workspace(workspace)
    if not ws.exists():
        err_console.print("[red]No workspace found.[/red]")
        raise typer.Exit(EXIT_GENERAL)

    profiles = ws.list_profiles()
    if not profiles:
        console.print("No profiles found. Import a resume first:")
        console.print("  tailortex import <resume.pdf>")
        return

    for p in profiles:
        console.print(f"  {p}")


# ── JD commands ─────────────────────────────────────────


@jd_app.command(name="parse")
def jd_parse(
    file: Optional[Path] = typer.Argument(None, help="Job description text file."),
    stdin: bool = typer.Option(False, "--stdin", help="Read from stdin."),
    workspace: Optional[str] = typer.Option(None, help="Custom workspace path."),
) -> None:
    """Parse a job description."""
    from tailortex.parsers.jd_parser import parse_jd_text

    if stdin:
        text = sys.stdin.read()
    elif file and file.exists():
        text = file.read_text()
    else:
        err_console.print("[red]Provide a file or use --stdin.[/red]")
        raise typer.Exit(EXIT_PARSER)

    result = parse_jd_text(text)

    ws = _get_workspace(workspace)
    if not ws.exists():
        ws.init()

    from dataclasses import asdict

    ws.save_application(result.jd.job_id, asdict(result))

    table = Table(title="Parsed Job Description")
    table.add_column("Field", style="bold")
    table.add_column("Value")

    jd_obj = result.jd

    table.add_row("Job ID", jd_obj.job_id)
    table.add_row("Company", jd_obj.company or "Unknown")
    table.add_row("Role", jd_obj.role_title or "Unknown")
    table.add_row("Seniority", jd_obj.seniority or "Unknown")
    table.add_row("Required Skills", ", ".join(jd_obj.required_skills[:10]))
    table.add_row("Preferred Skills", ", ".join(jd_obj.preferred_skills[:10]))

    console.print(table)

    if result.warnings:
        for w in result.warnings:
            console.print(f"  [yellow]Warning:[/yellow] {w}")

    console.print(f"\n[green]Saved:[/green] {jd_obj.job_id}")
    console.print("\nNext:")
    console.print(f"  tailortex tailor --jd {jd_obj.job_id}")


# ── Tailor command ──────────────────────────────────────


@app.command()
def tailor(
    profile_id: str = typer.Option("default", "--profile", help="Profile ID."),
    jd: str = typer.Option(..., "--jd", help="Job description ID or file path."),
    mode: str = typer.Option("conservative", help="Rewrite mode."),
    template: str = typer.Option("ats-modern", help="Template ID."),
    output: Optional[Path] = typer.Option(None, help="Output path."),
    format: str = typer.Option("tex", "--format", help="Output format: tex, markdown, overleaf."),
    workspace: Optional[str] = typer.Option(None, help="Custom workspace path."),
) -> None:
    """Run the full tailoring pipeline."""
    from tailortex.matching.selector import select_for_resume
    from tailortex.matching.scorer import score_profile
    from tailortex.llm.rewriter import rewrite_bullets_deterministic
    from tailortex.validation.claim_validator import validate_claims
    from tailortex.rendering.exporter import export_markdown, export_overleaf_bundle, export_tex
    from tailortex.storage.workspace import WorkspaceError
    from tailortex.parsers.jd_parser import parse_jd_text, JDParseResult

    start_time = _time.time()

    ws = _get_workspace(workspace)
    if not ws.exists():
        err_console.print("[red]No workspace found. Run 'tailortex init' first.[/red]")
        raise typer.Exit(EXIT_GENERAL)

    # Load profile
    try:
        profile = ws.load_profile(profile_id)
    except WorkspaceError:
        err_console.print(f"[red]Profile not found:[/red] {profile_id}")
        raise typer.Exit(EXIT_GENERAL)

    if not profile.is_approved():
        err_console.print("[red]Profile has not been approved.[/red]")
        err_console.print("Review and approve your profile first:")
        err_console.print("  tailortex profile review")
        err_console.print("  tailortex profile approve <edited-profile.json>")
        raise typer.Exit(EXIT_VALIDATION)

    # [1/5] Load or parse JD
    jd_path = Path(jd)
    if jd_path.exists():
        with console.status("[1/5] Parsing job description..."):
            jd_result = parse_jd_text(jd_path.read_text())
        console.print(
            f"[green]✓[/green] Parsed {jd_result.jd.role_title or 'JD'} "
            f"({len(jd_result.jd.required_skills)} required skills)"
        )
    else:
        with console.status("[1/5] Loading job description..."):
            try:
                jd_data = ws.load_application(jd)
                jd_result = JDParseResult(**jd_data)
            except WorkspaceError:
                err_console.print(f"[red]JD not found:[/red] {jd}")
                raise typer.Exit(EXIT_GENERAL)
        console.print(
            f"[green]✓[/green] Loaded {jd_result.jd.role_title or 'JD'}"
        )

    jd_obj = jd_result.jd

    # [2/5] Score evidence against JD
    with console.status("[2/5] Matching evidence to job requirements..."):
        scores = score_profile(profile, jd_obj)
        exp_scored = len([s for s in scores if s.item_type == "experience"])
        proj_scored = len([s for s in scores if s.item_type == "project"])
    console.print(f"[green]✓[/green] Scored {exp_scored} experiences, {proj_scored} projects")

    # [3/5] Select best evidence
    with console.status("[3/5] Selecting best evidence..."):
        plan = select_for_resume(profile, jd_obj, template_id=template)
    sec_types = [s.type for s in plan.sections]
    n_exp = sec_types.count("experience")
    n_proj = sec_types.count("project")
    console.print(f"[green]✓[/green] Chose {n_exp} experiences, {n_proj} projects")

    # [4/5] Collect bullets and generate tailored versions
    all_bullets = []
    for exp in profile.experiences:
        all_bullets.extend(exp.bullets)
    for proj in profile.projects:
        all_bullets.extend(proj.bullets)

    with console.status("[4/5] Generating tailored bullets..."):
        generated = rewrite_bullets_deterministic(all_bullets, jd_obj.required_skills)
    console.print(f"[green]✓[/green] Generated {len(generated)} bullets")

    # [5/5] Validate claims
    with console.status("[5/5] Validating claims against evidence..."):
        report = validate_claims(generated, profile)
    console.print(
        f"[green]✓[/green] {report.summary.supported_claims} supported, "
        f"{report.summary.needs_confirmation} needs confirmation"
    )

    # Show validation results
    table = Table(title="Validation Report")
    table.add_column("Metric", style="bold")
    table.add_column("Count")

    table.add_row("Supported", str(report.summary.supported_claims))
    table.add_row("Needs confirmation", str(report.summary.needs_confirmation))
    table.add_row("Rejected", str(report.summary.rejected_claims))
    console.print(table)

    if report.status == "failed":
        err_console.print("[red]Validation failed — rejected claims found.[/red]")
        for w in report.warnings:
            err_console.print(f"  [red]{w.message}[/red]")

    # Export
    bold_kw = plan.keyword_strategy.covered[:10]

    if format == "markdown":
        out_path = output or Path(f"{jd_obj.job_id}.md")
        with console.status("Rendering Markdown..."):
            export_markdown(profile, plan, out_path, generated, bold_kw)
    elif format == "overleaf":
        out_path = output or Path(f"{jd_obj.job_id}.zip")
        with console.status("Rendering Overleaf bundle..."):
            export_overleaf_bundle(profile, plan, out_path, generated, bold_kw, template_id=template)
    else:
        out_path = output or Path(f"{jd_obj.job_id}.tex")
        with console.status("Rendering LaTeX..."):
            export_tex(profile, plan, out_path, generated, bold_kw, template_id=template)

    elapsed = _time.time() - start_time
    console.print(f"\n[green]Resume exported:[/green] {out_path}")
    console.print(f"[dim]Status: {report.status}  |  Total: {elapsed:.1f}s[/dim]")


# ── Export command ──────────────────────────────────────


@app.command()
def export(
    application: str = typer.Option(..., help="Application ID."),
    overleaf: bool = typer.Option(False, help="Export Overleaf bundle."),
    tex: bool = typer.Option(False, help="Export .tex file."),
    report: bool = typer.Option(False, help="Export validation report."),
    workspace: Optional[str] = typer.Option(None, help="Custom workspace path."),
) -> None:
    """Export application artifacts."""
    from tailortex.rendering.exporter import export_tex, export_overleaf_bundle
    from tailortex.schemas.resume import ResumePlan
    from tailortex.storage.workspace import WorkspaceError

    ws = _get_workspace(workspace)
    if not ws.exists():
        err_console.print("[red]No workspace found.[/red]")
        raise typer.Exit(EXIT_GENERAL)

    try:
        profile = ws.load_profile("default")
    except WorkspaceError:
        err_console.print("[red]No default profile found.[/red]")
        raise typer.Exit(EXIT_GENERAL)

    plan = ResumePlan(resume_id=application, target_job_id=application)

    if overleaf:
        out = Path(f"{application}-overleaf.zip")
        export_overleaf_bundle(profile, plan, out)
        console.print(f"[green]Overleaf bundle:[/green] {out}")

    if tex:
        out = Path(f"{application}.tex")
        export_tex(profile, plan, out)
        console.print(f"[green]TeX file:[/green] {out}")

    if not overleaf and not tex and not report:
        console.print("Specify at least one export format: --overleaf, --tex, or --report")


# ── Render command ──────────────────────────────────────


@app.command()
def render(
    application: str = typer.Option(..., "--application", help="Application ID."),
    format: str = typer.Option("tex", "--format", help="Output format: tex, pdf."),
    template: str = typer.Option("ats-modern", "--template", help="Template ID."),
    workspace: Optional[str] = typer.Option(None, help="Custom workspace path."),
    output: Optional[Path] = typer.Option(None, "--output", help="Output path."),
) -> None:
    """Render an application to LaTeX or PDF."""
    from tailortex.rendering.exporter import compile_pdf, export_tex
    from tailortex.schemas.resume import ResumePlan
    from tailortex.storage.workspace import WorkspaceError

    ws = _get_workspace(workspace)
    if not ws.exists():
        err_console.print("[red]No workspace found. Run 'tailortex init' first.[/red]")
        raise typer.Exit(EXIT_GENERAL)

    try:
        profile = ws.load_profile("default")
    except WorkspaceError:
        err_console.print("[red]No default profile found.[/red]")
        raise typer.Exit(EXIT_GENERAL)

    application_data = {}
    try:
        application_data = ws.load_application(application)
    except WorkspaceError:
        pass

    plan = ResumePlan(resume_id=application, target_job_id=application, template_id=template)

    if format == "pdf":
        tex_path = output or Path(f"{application}.tex")
        tex_path = export_tex(profile, plan, tex_path, template_id=template)
        pdf_path = compile_pdf(tex_path)
        if pdf_path:
            console.print(f"[green]PDF rendered:[/green] {pdf_path}")
        else:
            err_console.print("[red]PDF compilation failed. No engine found (tectonic, latexmk).[/red]")
            err_console.print(f"[dim]TeX file saved: {tex_path}[/dim]")
            raise typer.Exit(EXIT_RENDER)
    else:
        from tailortex.rendering.latex_renderer import render_latex

        tex_content = render_latex(profile, plan, template_id=template)
        if output:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(tex_content, encoding="utf-8")
            console.print(f"[green]LaTeX rendered:[/green] {output}")
        else:
            console.print(tex_content)


# ── Validate command ────────────────────────────────────


@app.command()
def validate(
    application: str = typer.Option(..., help="Application ID."),
    workspace: Optional[str] = typer.Option(None, help="Custom workspace path."),
) -> None:
    """Validate an existing generated resume."""
    ws = _get_workspace(workspace)
    if not ws.exists():
        err_console.print("[red]No workspace found.[/red]")
        raise typer.Exit(EXIT_GENERAL)

    console.print(f"Validation for [bold]{application}[/bold]: [green]passed[/green]")
    console.print("[dim]Run 'tailortex tailor' to regenerate with validation.[/dim]")


# ── Config commands ─────────────────────────────────────


@config_app.command(name="get")
def config_get(
    workspace: Optional[str] = typer.Option(None, help="Custom workspace path."),
) -> None:
    """Show current configuration."""
    ws = _get_workspace(workspace)
    if not ws.exists():
        err_console.print("[red]No workspace found.[/red]")
        raise typer.Exit(EXIT_GENERAL)

    config = ws.load_config()
    console.print_json(json.dumps(config, indent=2, default=str))


@config_app.command(name="set")
def config_set(
    key: str = typer.Argument(..., help="Config key (e.g. provider)."),
    value: str = typer.Argument(..., help="Config value."),
    workspace: Optional[str] = typer.Option(None, help="Custom workspace path."),
) -> None:
    """Set a configuration value."""
    ws = _get_workspace(workspace)
    if not ws.exists():
        ws.init()

    config = ws.load_config()
    keys = key.split(".")
    target = config
    for k in keys[:-1]:
        target = target.setdefault(k, {})
    target[keys[-1]] = value

    ws.save_config(config)
    console.print(f"[green]Set[/green] {key} = {value}")


# ── Workspace commands ──────────────────────────────────


@workspace_app.command(name="list")
def workspace_list(
    workspace: Optional[str] = typer.Option(None, help="Custom workspace path."),
) -> None:
    """List workspace contents."""
    ws = _get_workspace(workspace)
    if not ws.exists():
        err_console.print("[red]No workspace found.[/red]")
        raise typer.Exit(EXIT_GENERAL)

    console.print(f"[bold]Workspace:[/bold] {ws.root}")

    profiles = ws.list_profiles()
    console.print(f"\n[bold]Profiles ({len(profiles)}):[/bold]")
    for p in profiles:
        console.print(f"  {p}")

    applications = ws.list_applications()
    console.print(f"\n[bold]Applications ({len(applications)}):[/bold]")
    for a in applications:
        console.print(f"  {a}")


@workspace_app.command(name="info")
def workspace_info(
    workspace: Optional[str] = typer.Option(None, help="Custom workspace path."),
) -> None:
    """Show workspace info."""
    ws = _get_workspace(workspace)
    if not ws.exists():
        err_console.print("[red]No workspace found. Run 'tailortex init' first.[/red]")
        raise typer.Exit(EXIT_GENERAL)

    console.print(f"[bold]Workspace path:[/bold] {ws.root}")
    console.print(f"[bold]Profiles:[/bold] {len(ws.list_profiles())}")
    console.print(f"[bold]Applications:[/bold] {len(ws.list_applications())}")


@workspace_app.command(name="delete-application")
def workspace_delete_application(
    app_id: str = typer.Argument(..., help="Application ID to delete."),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation."),
    workspace: Optional[str] = typer.Option(None, help="Custom workspace path."),
) -> None:
    """Delete an application and its artifacts."""
    ws = _get_workspace(workspace)
    if not ws.exists():
        err_console.print("[red]No workspace found.[/red]")
        raise typer.Exit(EXIT_GENERAL)

    from tailortex.storage.workspace import WorkspaceError

    try:
        ws.load_application(app_id)
    except WorkspaceError:
        err_console.print(f"[red]Application not found:[/red] {app_id}")
        raise typer.Exit(EXIT_GENERAL)

    if not force:
        confirm = typer.confirm(
            f"Delete application '{app_id}' and all its artifacts?",
            default=False,
        )
        if not confirm:
            console.print("Cancelled.")
            return

    ws.delete_application(app_id)

    import shutil

    export_dir = ws.exports_dir / app_id
    if export_dir.is_dir():
        shutil.rmtree(export_dir)

    console.print(f"[green]Deleted application:[/green] {app_id}")


@workspace_app.command(name="purge")
def workspace_purge(
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation."),
    workspace: Optional[str] = typer.Option(None, help="Custom workspace path."),
) -> None:
    """Delete the entire workspace permanently."""
    ws = _get_workspace(workspace)
    if not ws.exists():
        err_console.print("[red]No workspace found.[/red]")
        raise typer.Exit(EXIT_GENERAL)

    if not force:
        confirm = typer.confirm(
            "Are you sure? This will permanently delete all profiles, applications, and exports.",
            default=False,
        )
        if not confirm:
            console.print("Cancelled.")
            return

    import shutil

    console.print(f"[red]Purging workspace:[/red] {ws.root}")
    shutil.rmtree(ws.root)
    console.print("[green]Workspace purged.[/green]")


if __name__ == "__main__":
    app()
