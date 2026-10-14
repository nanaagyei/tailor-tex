"""TailorTex API — local HTTP server for the web UI."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from tailortex import __version__
from tailortex.parsers.extractors import extract_text
from tailortex.parsers.jd_parser import parse_jd_text
from tailortex.schemas.job import ParsedJobDescription
from tailortex.parsers.resume_parser import parse_resume_text
from tailortex.schemas.profile import CanonicalProfile
from tailortex.storage.workspace import Workspace, WorkspaceError

app = FastAPI(
    title="TailorTex API",
    version=__version__,
    description="Local API server for the TailorTex web UI.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _ws() -> Workspace:
    ws = Workspace()
    if not ws.exists():
        ws.init()
    return ws


# ── Health ──────────────────────────────────────────────


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "version": __version__}


# ── Profiles ────────────────────────────────────────────


@app.get("/profiles")
async def list_profiles() -> list[str]:
    return _ws().list_profiles()


@app.get("/profiles/{profile_id}")
async def get_profile(profile_id: str) -> dict[str, Any]:
    try:
        profile = _ws().load_profile(profile_id)
        return profile.model_dump()
    except WorkspaceError:
        raise HTTPException(status_code=404, detail=f"Profile not found: {profile_id}")


@app.post("/profiles")
async def save_profile(profile: CanonicalProfile) -> dict[str, str]:
    _ws().save_profile(profile)
    return {"status": "saved", "profile_id": profile.profile_id}


@app.delete("/profiles/{profile_id}")
async def delete_profile(profile_id: str) -> dict[str, str]:
    try:
        _ws().delete_profile(profile_id)
        return {"status": "deleted", "profile_id": profile_id}
    except WorkspaceError:
        raise HTTPException(status_code=404, detail=f"Profile not found: {profile_id}")


# ── Import ──────────────────────────────────────────────


@app.post("/import")
async def import_resume(file: UploadFile = File(...)) -> dict[str, Any]:
    """Import a resume file and parse into a draft profile."""
    import tempfile

    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    suffix = Path(file.filename).suffix
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        try:
            result = extract_text(tmp_path)
        except (ValueError, ImportError) as e:
            raise HTTPException(status_code=422, detail=str(e))

        if not result.text:
            raise HTTPException(status_code=422, detail="Could not extract text from file")

        draft = parse_resume_text(result.text)
        return {
            "status": "imported",
            "draft": draft.profile.model_dump(),
            "warnings": result.diagnostics + [w.message for w in draft.warnings],
        }
    finally:
        tmp_path.unlink(missing_ok=True)


# ── JD Parsing ──────────────────────────────────────────


class JDParseRequest(BaseModel):
    text: str
    company: str | None = None
    role_title: str | None = None


@app.post("/jd/parse")
async def parse_jd(req: JDParseRequest) -> dict[str, Any]:
    result = parse_jd_text(req.text, company=req.company, role_title=req.role_title)
    ws = _ws()
    jd_data = result.jd.model_dump()
    ws.save_application(result.jd.job_id, jd_data)
    return jd_data


# ── Applications ────────────────────────────────────────


@app.get("/applications")
async def list_applications() -> list[str]:
    return _ws().list_applications()


@app.get("/applications/{app_id}")
async def get_application(app_id: str) -> dict[str, Any]:
    try:
        return _ws().load_application(app_id)
    except WorkspaceError:
        raise HTTPException(status_code=404, detail=f"Application not found: {app_id}")


@app.delete("/applications/{app_id}")
async def delete_application(app_id: str) -> dict[str, str]:
    try:
        _ws().delete_application(app_id)
        return {"status": "deleted", "app_id": app_id}
    except WorkspaceError:
        raise HTTPException(status_code=404, detail=f"Application not found: {app_id}")


# ── Tailoring ───────────────────────────────────────────


class TailorRequest(BaseModel):
    profile_id: str = "default"
    jd_id: str
    mode: str = "conservative"
    template_id: str = "ats-modern"


@app.post("/tailor")
async def tailor_resume(req: TailorRequest) -> dict[str, Any]:
    from tailortex.llm.rewriter import rewrite_bullets_deterministic
    from tailortex.matching.selector import select_for_resume
    from tailortex.validation.claim_validator import validate_claims

    ws = _ws()

    try:
        profile = ws.load_profile(req.profile_id)
    except WorkspaceError:
        raise HTTPException(status_code=404, detail=f"Profile not found: {req.profile_id}")

    try:
        jd_data = ws.load_application(req.jd_id)
        jd = ParsedJobDescription(**jd_data)
    except WorkspaceError:
        raise HTTPException(status_code=404, detail=f"JD not found: {req.jd_id}")

    plan = select_for_resume(profile, jd, template_id=req.template_id)

    all_bullets = []
    for exp in profile.experiences:
        all_bullets.extend(exp.bullets)
    for proj in profile.projects:
        all_bullets.extend(proj.bullets)

    generated = rewrite_bullets_deterministic(all_bullets, jd.required_skills)
    report = validate_claims(generated, profile)

    return {
        "plan": plan.model_dump(),
        "generated_bullets": [g.model_dump() for g in generated],
        "validation": report.model_dump(),
    }


# ── Rendering ───────────────────────────────────────────


class RenderRequest(BaseModel):
    profile_id: str = "default"
    jd_id: str
    template_id: str = "ats-modern"


@app.post("/render")
async def render_resume(req: RenderRequest) -> dict[str, str]:
    from tailortex.matching.selector import select_for_resume
    from tailortex.rendering.latex_renderer import render_latex

    ws = _ws()

    try:
        profile = ws.load_profile(req.profile_id)
    except WorkspaceError:
        raise HTTPException(status_code=404, detail=f"Profile not found: {req.profile_id}")

    try:
        jd_data = ws.load_application(req.jd_id)
        jd = ParsedJobDescription(**jd_data)
    except WorkspaceError:
        raise HTTPException(status_code=404, detail=f"JD not found: {req.jd_id}")

    plan = select_for_resume(profile, jd, template_id=req.template_id)
    tex = render_latex(profile, plan)

    return {"tex": tex}


# ── Config ──────────────────────────────────────────────


@app.get("/config")
async def get_config() -> dict[str, Any]:
    return _ws().load_config()


@app.put("/config")
async def update_config(config: dict[str, Any]) -> dict[str, str]:
    _ws().save_config(config)
    return {"status": "saved"}
