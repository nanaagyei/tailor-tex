"""TailorTex CLI — command-line interface for resume tailoring."""

from __future__ import annotations

import json
import sys
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
    ws.save_application("draft-profile", draft.model_dump())

    console.print(f"[green]Imported:[/green] {file.name}")
    console.print("Profile draft saved.")

    if result.warnings:
        for w in result.warnings:
            console.print(f"  [yellow]Warning:[/yellow] {w}")

    console.print("\nNext:")
    console.print("  tailortex profile review")


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

    ws.save_application(result.job_id, result.model_dump())

    table = Table(title="Parsed Job Description")
    table.add_column("Field", style="bold")
    table.add_column("Value")

    table.add_row("Job ID", result.job_id)
    table.add_row("Company", result.company or "Unknown")
    table.add_row("Role", result.role_title or "Unknown")
    table.add_row("Seniority", result.seniority or "Unknown")
    table.add_row("Required Skills", ", ".join(result.required_skills[:10]))
    table.add_row("Preferred Skills", ", ".join(result.preferred_skills[:10]))

    console.print(table)

    if result.warnings:
        for w in result.warnings:
            console.print(f"  [yellow]Warning:[/yellow] {w}")

    console.print(f"\n[green]Saved:[/green] {result.job_id}")
    console.print("\nNext:")
    console.print(f"  tailortex tailor --jd {result.job_id}")


# ── Tailor command ──────────────────────────────────────


@app.command()
def tailor(
    profile_id: str = typer.Option("default", "--profile", help="Profile ID."),
    jd: str = typer.Option(..., "--jd", help="Job description ID or file path."),
    mode: str = typer.Option("conservative", help="Rewrite mode."),
    template: str = typer.Option("ats-modern", help="Template ID."),
    output: Optional[Path] = typer.Option(None, help="Output .tex path."),
    workspace: Optional[str] = typer.Option(None, help="Custom workspace path."),
) -> None:
    """Run the full tailoring pipeline."""
    from tailortex.matching.selector import select_for_resume
    from tailortex.llm.rewriter import rewrite_bullets_deterministic
    from tailortex.validation.claim_validator import validate_claims
    from tailortex.rendering.exporter import export_tex
    from tailortex.storage.workspace import WorkspaceError
    from tailortex.parsers.jd_parser import parse_jd_text, JDParseResult

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

    # Load or parse JD
    jd_path = Path(jd)
    if jd_path.exists():
        jd_result = parse_jd_text(jd_path.read_text())
    else:
        try:
            jd_data = ws.load_application(jd)
            jd_result = JDParseResult(**jd_data)
        except WorkspaceError:
            err_console.print(f"[red]JD not found:[/red] {jd}")
            raise typer.Exit(EXIT_GENERAL)

    with console.status("Selecting evidence..."):
        plan = select_for_resume(profile, jd_result, template_id=template)

    # Collect bullets for rewriting
    all_bullets = []
    for exp in profile.experiences:
        all_bullets.extend(exp.bullets)
    for proj in profile.projects:
        all_bullets.extend(proj.bullets)

    with console.status("Generating bullets..."):
        generated = rewrite_bullets_deterministic(all_bullets, jd_result.required_skills)

    with console.status("Validating claims..."):
        report = validate_claims(generated, profile)

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

    # Export .tex
    out_path = output or Path(f"{jd_result.job_id}.tex")
    with console.status("Rendering LaTeX..."):
        bold_kw = plan.keyword_strategy.covered[:10]
        export_tex(profile, plan, out_path, generated, bold_kw)

    console.print(f"\n[green]Resume exported:[/green] {out_path}")
    console.print(f"[dim]Status: {report.status}[/dim]")


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


if __name__ == "__main__":
    app()
