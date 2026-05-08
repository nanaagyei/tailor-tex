"""Evidence selector — picks top-N items for the resume plan."""

from __future__ import annotations

from tailortex.matching.scorer import MatchScore, score_profile
from tailortex.schemas.job import ParsedJobDescription
from tailortex.schemas.profile import CanonicalProfile
from tailortex.schemas.resume import (
    DoNotInsert,
    KeywordStrategy,
    ResumePlan,
    SectionPlan,
)


def select_for_resume(
    profile: CanonicalProfile,
    jd: ParsedJobDescription,
    max_experiences: int = 3,
    max_projects: int = 2,
    template_id: str = "ats-modern",
) -> ResumePlan:
    """Select the best experiences and projects for a resume plan.

    Also computes keyword coverage strategy — never includes skills
    without approved evidence.
    """
    scores = score_profile(profile, jd)

    # Separate by type
    exp_scores = [s for s in scores if s.item_type == "experience"]
    proj_scores = [s for s in scores if s.item_type == "project"]

    # Select top items
    selected_exp = exp_scores[:max_experiences]
    selected_proj = proj_scores[:max_projects]

    # Build sections
    sections: list[SectionPlan] = []

    for score in selected_exp:
        exp = next(e for e in profile.experiences if e.id == score.item_id)
        sections.append(
            SectionPlan(
                type="experience",
                source_ids=[exp.id],
                selected_bullet_ids=[b.id for b in exp.bullets],
                reason=f"Match score: {score.total_score:.2f}. "
                f"Matched skills: {', '.join(score.matched_skills) or 'none'}.",
            )
        )

    for score in selected_proj:
        proj = next(p for p in profile.projects if p.id == score.item_id)
        sections.append(
            SectionPlan(
                type="project",
                source_ids=[proj.id],
                selected_bullet_ids=[b.id for b in proj.bullets],
                reason=f"Match score: {score.total_score:.2f}. "
                f"Matched skills: {', '.join(score.matched_skills) or 'none'}.",
            )
        )

    # Add education if present
    if profile.education:
        sections.append(
            SectionPlan(
                type="education",
                source_ids=[e.id for e in profile.education],
            )
        )

    # Keyword strategy
    keyword_strategy = _compute_keyword_strategy(profile, jd, scores)

    resume_id = f"resume_{jd.job_id}"
    return ResumePlan(
        resume_id=resume_id,
        target_job_id=jd.job_id,
        template_id=template_id,
        sections=sections,
        keyword_strategy=keyword_strategy,
    )


def _compute_keyword_strategy(
    profile: CanonicalProfile,
    jd: ParsedJobDescription,
    scores: list[MatchScore],
) -> KeywordStrategy:
    """Determine keyword coverage — which skills are covered, missing, or blocked."""
    # Collect all skills from the profile
    profile_skills_lower = set()
    for skill in profile.skills:
        profile_skills_lower.add(skill.name.lower())
    for exp in profile.experiences:
        for bullet in exp.bullets:
            for s in bullet.skills:
                profile_skills_lower.add(s.lower())
    for proj in profile.projects:
        for s in proj.skills:
            profile_skills_lower.add(s.lower())

    all_jd_skills = jd.required_skills + jd.preferred_skills
    covered: list[str] = []
    not_covered: list[str] = []
    do_not_insert: list[DoNotInsert] = []

    for skill in all_jd_skills:
        if skill.lower() in profile_skills_lower:
            covered.append(skill)
        else:
            not_covered.append(skill)
            do_not_insert.append(
                DoNotInsert(
                    keyword=skill,
                    reason=f"No approved evidence for '{skill}' in canonical profile.",
                )
            )

    return KeywordStrategy(
        covered=covered,
        not_covered=not_covered,
        do_not_insert=do_not_insert,
    )
